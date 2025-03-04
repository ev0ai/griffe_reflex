# This module contains all the logic for loading API data from sources or compiled modules.

from __future__ import annotations

from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, cast

from _griffe.agents.inspector import inspect
from _griffe.agents.visitor import visit
from _griffe.collections import LinesCollection, ModulesCollection
from _griffe.enumerations import Kind
from _griffe.exceptions import (
    AliasResolutionError,
    CyclicAliasError,
    LoadingError,
    UnimportableModuleError,
)
from _griffe.expressions import ExprName
from _griffe.extensions.base import Extensions, load_extensions
from _griffe.finder import ModuleFinder, NamespacePackage, Package
from _griffe.git import tmp_worktree
from _griffe.importer import dynamic_import
from _griffe.logger import logger
from _griffe.merger import merge_stubs
from _griffe.models import Alias, Module, Object
from _griffe.stats import Stats

if TYPE_CHECKING:
    from collections.abc import Sequence

    from _griffe.docstrings.parsers import DocstringStyle
    from _griffe.enumerations import Parser


class GriffeLoader:
    """The Griffe loader, allowing to load data from modules."""

    ignored_modules: ClassVar[set[str]] = {"debugpy", "_pydev"}
    """Special modules to ignore when loading.

    For example, `debugpy` and `_pydev` are used when debugging with VSCode and should generally never be loaded.
    """

    def __init__(
        self,
        *,
        extensions: Extensions | None = None,
        search_paths: Sequence[str | Path] | None = None,
        docstring_parser: DocstringStyle | Parser | None = None,
        docstring_options: dict[str, Any] | None = None,
        lines_collection: LinesCollection | None = None,
        modules_collection: ModulesCollection | None = None,
        allow_inspection: bool = True,
        force_inspection: bool = False,
        store_source: bool = True,
    ) -> None:
        """Initialize the loader.

        Parameters:
            extensions: The extensions to use.
            search_paths: The paths to search into.
            docstring_parser: The docstring parser to use. By default, no parsing is done.
            docstring_options: Additional docstring parsing options.
            lines_collection: A collection of source code lines.
            modules_collection: A collection of modules.
            allow_inspection: Whether to allow inspecting modules when visiting them is not possible.
            store_source: Whether to store code source in the lines collection.
        """
        self.extensions: Extensions = extensions or load_extensions()
        """Loaded Griffe extensions."""
        self.docstring_parser: DocstringStyle | Parser | None = docstring_parser
        """Selected docstring parser."""
        self.docstring_options: dict[str, Any] = docstring_options or {}
        """Configured parsing options."""
        self.lines_collection: LinesCollection = lines_collection or LinesCollection()
        """Collection of source code lines."""
        self.modules_collection: ModulesCollection = modules_collection or ModulesCollection()
        """Collection of modules."""
        self.allow_inspection: bool = allow_inspection
        """Whether to allow inspecting (importing) modules for which we can't find sources."""
        self.force_inspection: bool = force_inspection
        """Whether to force inspecting (importing) modules, even when sources were found."""
        self.store_source: bool = store_source
        """Whether to store source code in the lines collection."""
        self.finder: ModuleFinder = ModuleFinder(search_paths)
        """The module source finder."""
        self._time_stats: dict = {
            "time_spent_visiting": 0,
            "time_spent_inspecting": 0,
        }

    def load(
        self,
        objspec: str | Path | None = None,
        /,
        *,
        submodules: bool = True,
        try_relative_path: bool = True,
        find_stubs_package: bool = False,
    ) -> Object | Alias:
        """Load an object as a Griffe object, given its Python or file path.

        Note that this will load the whole object's package,
        and return only the specified object.
        The rest of the package can be accessed from the returned object
        with regular methods and properties (`parent`, `members`, etc.).

        Examples:
            >>> loader.load("griffe.Module")
            Alias("Module", "_griffe.models.Module")

        Parameters:
            objspec: The Python path of an object, or file path to a module.
            submodules: Whether to recurse on the submodules.
                This parameter only makes sense when loading a package (top-level module).
            try_relative_path: Whether to try finding the module as a relative path.
            find_stubs_package: Whether to search for stubs-only package.
                If both the package and its stubs are found, they'll be merged together.
                If only the stubs are found, they'll be used as the package itself.

        Raises:
            LoadingError: When loading a module failed for various reasons.
            ModuleNotFoundError: When a module was not found and inspection is disallowed.

        Returns:
            A Griffe object.
        """
        obj_path: str
        package = None
        top_module = None

        # We always start by searching paths on the disk,
        # even if inspection is forced.
        logger.debug("Searching path(s) for %s", objspec)
        try:
            obj_path, package = self.finder.find_spec(
                objspec,  # type: ignore[arg-type]
                try_relative_path=try_relative_path,
                find_stubs_package=find_stubs_package,
            )
        except ModuleNotFoundError:
            # If we couldn't find paths on disk and inspection is disabled,
            # re-raise ModuleNotFoundError.
            logger.debug("Could not find path for %s on disk", objspec)
            if not (self.allow_inspection or self.force_inspection):
                raise

            # Otherwise we try to dynamically import the top-level module.
            obj_path = str(objspec)
            top_module_name = obj_path.split(".", 1)[0]
            logger.debug("Trying to dynamically import %s", top_module_name)
            top_module_object = dynamic_import(top_module_name, self.finder.search_paths)

            try:
                top_module_path = top_module_object.__path__
                if not top_module_path:
                    raise ValueError(f"Module {top_module_name} has no paths set")  # noqa: TRY301
            except (AttributeError, ValueError):
                # If the top-level module has no `__path__`, we inspect it as-is,
                # and do not try to recurse into submodules (there shouldn't be any in builtin/compiled modules).
                logger.debug("Module %s has no paths set (built-in module?). Inspecting it as-is.", top_module_name)
                top_module = self._inspect_module(top_module_name)
                self.modules_collection.set_member(top_module.path, top_module)
                return self._post_load(top_module, obj_path)

            # We found paths, and use them to build our intermediate Package or NamespacePackage struct.
            logger.debug("Module %s has paths set: %s", top_module_name, top_module_path)
            top_module_path = [Path(path) for path in top_module_path]
            if len(top_module_path) > 1:
                package = NamespacePackage(top_module_name, top_module_path)
            else:
                package = Package(top_module_name, top_module_path[0])

        # We have an intermediate package, and an object path: we're ready to load.
        logger.debug("Found %s: loading", objspec)
        try:
            top_module = self._load_package(package, submodules=submodules)
        except LoadingError:
            logger.exception("Could not load package %s", package)
            raise

        return self._post_load(top_module, obj_path)

    def _post_load(self, module: Module, obj_path: str) -> Object | Alias:
        # Pre-emptively expand exports (`__all__` values),
        # as well as wildcard imports (without ever loading additional packages).
        # This is a best-effort to return the most correct API data
        # before firing the `on_package_loaded` event.
        #
        # Packages that wildcard imports from external, non-loaded packages
        # will still have incomplete data, requiring subsequent calls to
        # `load()` and/or `resolve_aliases()`.
        self.expand_exports(module)
        self.expand_wildcards(module, external=False)
        # Package is loaded, we now retrieve the initially requested object and return it.
        obj = self.modules_collection.get_member(obj_path)
        self.extensions.call("on_package_loaded", pkg=module, loader=self)
        return obj

    def resolve_aliases(
        self,
        *,
        implicit: bool = False,
        external: bool | None = None,
        max_iterations: int | None = None,
    ) -> tuple[set[str], int]:
        """Resolve aliases.

        Parameters:
            implicit: When false, only try to resolve an alias if it is explicitly exported.
            external: When false, don't try to load unspecified modules to resolve aliases.
            max_iterations: Maximum number of iterations on the loader modules collection.

        Returns:
            The unresolved aliases and the number of iterations done.
        """
        if max_iterations is None:
            max_iterations = float("inf")  # type: ignore[assignment]
        prev_unresolved: set[str] = set()
        unresolved: set[str] = set("0")  # init to enter loop
        iteration = 0
        collection = self.modules_collection.members

        # Before resolving aliases, we try to expand wildcard imports again
        # (this was already done in `_post_load()`),
        # this time with the user-configured `external` setting,
        # and with potentially more packages loaded in the collection,
        # allowing to resolve more aliases.
        for wildcards_module in list(collection.values()):
            self.expand_wildcards(wildcards_module, external=external)

        load_failures: set[str] = set()
        while unresolved and unresolved != prev_unresolved and iteration < max_iterations:  # type: ignore[operator]
            prev_unresolved = unresolved - {"0"}
            unresolved = set()
            resolved: set[str] = set()
            iteration += 1
            for module_name in list(collection.keys()):
                module = collection[module_name]
                next_resolved, next_unresolved = self.resolve_module_aliases(
                    module,
                    implicit=implicit,
                    external=external,
                    load_failures=load_failures,
                )
                resolved |= next_resolved
                unresolved |= next_unresolved
            logger.debug(
                "Iteration %s finished, %s aliases resolved, still %s to go",
                iteration,
                len(resolved),
                len(unresolved),
            )
        return unresolved, iteration

    def expand_exports(self, module: Module, seen: set | None = None) -> None:
        """Expand exports: try to recursively expand all module exports (`__all__` values).

        See also: [`Module.exports`][griffe.Module.exports].

        Parameters:
            module: The module to recurse on.
            seen: Used to avoid infinite recursion.
        """
        seen = seen or set()
        seen.add(module.path)
        if module.exports is None:
            return

        expanded = set()
        for export in module.exports:
            # It's a name: we resolve it, get the module it comes from,
            # recurse into it, and add its exports to the current ones.
            if isinstance(export, ExprName):
                module_path = export.canonical_path.rsplit(".", 1)[0]  # remove trailing .__all__
                try:
                    next_module = self.modules_collection.get_member(module_path)
                except KeyError:
                    logger.debug("Cannot expand '%s', try pre-loading corresponding package", export.canonical_path)
                    continue
                if next_module.path not in seen:
                    self.expand_exports(next_module, seen)
                    try:
                        expanded |= next_module.exports
                    except TypeError:
                        logger.warning("Unsupported item in %s.__all__: %s (use strings only)", module.path, export)
            # It's a string, simply add it to the current exports.
            else:
                expanded.add(export)
        module.exports = expanded

        # Make sure to expand exports in all modules.
        for submodule in module.modules.values():
            if not submodule.is_alias and submodule.path not in seen:
                self.expand_exports(submodule, seen)

    def expand_wildcards(
        self,
        obj: Object,
        *,
        external: bool | None = None,
        seen: set | None = None,
    ) -> None:
        """Expand wildcards: try to recursively expand all found wildcards.

        See also: [`Alias.wildcard`][griffe.Alias.wildcard].

        Parameters:
            obj: The object and its members to recurse on.
            external: When true, try to load unspecified modules to expand wildcards.
            seen: Used to avoid infinite recursion.
        """
        expanded = []
        to_remove = []
        seen = seen or set()
        seen.add(obj.path)

        # First we expand wildcard imports and store the objects in a temporary `expanded` variable,
        # while also keeping track of the members representing wildcard import, to remove them later.
        for member in obj.members.values():
            # Handle a wildcard.
            if member.is_alias and member.wildcard:  # type: ignore[union-attr]  # we know it's an alias
                package = member.wildcard.split(".", 1)[0]  # type: ignore[union-attr]
                not_loaded = obj.package.path != package and package not in self.modules_collection

                # Try loading the (unknown) package containing the wildcard importe module (if allowed to).
                if not_loaded:
                    if external is False or (external is None and package != f"_{obj.package.name}"):
                        continue
                    try:
                        self.load(package, try_relative_path=False)
                    except (ImportError, LoadingError) as error:
                        logger.debug("Could not expand wildcard import %s in %s: %s", member.name, obj.path, error)
                        continue

                # Try getting the module from which every public object is imported.
                try:
                    target = self.modules_collection.get_member(member.target_path)  # type: ignore[union-attr]
                except KeyError:
                    logger.debug(
                        "Could not expand wildcard import %s in %s: %s not found in modules collection",
                        member.name,
                        obj.path,
                        cast(Alias, member).target_path,
                    )
                    continue

                # Recurse into this module, expanding wildcards there before collecting everything.
                if target.path not in seen:
                    try:
                        self.expand_wildcards(target, external=external, seen=seen)
                    except (AliasResolutionError, CyclicAliasError) as error:
                        logger.debug("Could not expand wildcard import %s in %s: %s", member.name, obj.path, error)
                        continue

                # Collect every imported object.
                expanded.extend(self._expand_wildcard(member))  # type: ignore[arg-type]
                to_remove.append(member.name)

            # Recurse in unseen submodules.
            elif not member.is_alias and member.is_module and member.path not in seen:
                self.expand_wildcards(member, external=external, seen=seen)  # type: ignore[arg-type]

        # Then we remove the members representing wildcard imports.
        for name in to_remove:
            obj.del_member(name)

        # Finally we process the collected objects.
        for new_member, alias_lineno, alias_endlineno in expanded:
            overwrite = False
            already_present = new_member.name in obj.members
            self_alias = new_member.is_alias and cast(Alias, new_member).target_path == f"{obj.path}.{new_member.name}"

            # If a member with the same name is already present in the current object,
            # we only overwrite it if the alias is imported lower in the module
            # (meaning that the alias takes precedence at runtime).
            if already_present:
                old_member = obj.get_member(new_member.name)
                old_lineno = old_member.alias_lineno if old_member.is_alias else old_member.lineno
                overwrite = alias_lineno > (old_lineno or 0)  # type: ignore[operator]

            # 1. If the expanded member is an alias with a target path equal to its own path, we stop.
            #    This situation can arise because of Griffe's mishandling of (abusive) wildcard imports.
            #    We have yet to check how Python handles this itself, or if there's an algorithm
            #    that we could follow to untangle back-and-forth wildcard imports.
            # 2. If the expanded member was already present and we decided not to overwrite it, we stop.
            # 3. Otherwise we proceed further.
            if not self_alias and (not already_present or overwrite):
                alias = Alias(
                    new_member.name,
                    new_member,
                    lineno=alias_lineno,
                    endlineno=alias_endlineno,
                    parent=obj,  # type: ignore[arg-type]
                )
                # Special case: we avoid overwriting a submodule with an alias pointing to it.
                # Griffe suffers from this design flaw where an object cannot store both
                # a submodule and a member of the same name, while this poses (almost) no issue in Python.
                # We at least prevent this case where a submodule is overwritten by an imported version of itself.
                if already_present:
                    prev_member = obj.get_member(new_member.name)
                    with suppress(AliasResolutionError, CyclicAliasError):
                        if prev_member.is_module:
                            if prev_member.is_alias:
                                prev_member = prev_member.final_target
                            if alias.final_target is prev_member:
                                # Alias named after the module it targets: skip to avoid cyclic aliases.
                                continue

                # Everything went right (supposedly), we add the alias as a member of the current object.
                obj.set_member(new_member.name, alias)
                self.extensions.call("on_wildcard_expansion", alias=alias, loader=self)

    def resolve_module_aliases(
        self,
        obj: Object | Alias,
        *,
        implicit: bool = False,
        external: bool | None = None,
        seen: set[str] | None = None,
        load_failures: set[str] | None = None,
    ) -> tuple[set[str], set[str]]:
        """Follow aliases: try to recursively resolve all found aliases.

        Parameters:
            obj: The object and its members to recurse on.
            implicit: When false, only try to resolve an alias if it is explicitly exported.
            external: When false, don't try to load unspecified modules to resolve aliases.
            seen: Used to avoid infinite recursion.
            load_failures: Set of external packages we failed to load (to prevent retries).

        Returns:
            Both sets of resolved and unresolved aliases.
        """
        resolved = set()
        unresolved = set()
        if load_failures is None:
            load_failures = set()
        seen = seen or set()
        seen.add(obj.path)

        for member in obj.members.values():
            # Handle aliases.
            if member.is_alias:
                if member.wildcard or member.resolved:  # type: ignore[union-attr]
                    continue
                if not implicit and not member.is_exported:
                    continue

                # Try resolving the alias. If it fails, check if it is because it comes
                # from an external package, and decide if we should load that package
                # to allow the alias to be resolved at the next iteration (maybe).
                try:
                    member.resolve_target()  # type: ignore[union-attr]
                except AliasResolutionError as error:
                    target = error.alias.target_path
                    unresolved.add(member.path)
                    package = target.split(".", 1)[0]
                    load_module = (
                        (external is True or (external is None and package == f"_{obj.package.name}"))
                        and package not in load_failures
                        and obj.package.path != package
                        and package not in self.modules_collection
                    )
                    if load_module:
                        logger.debug("Failed to resolve alias %s -> %s", member.path, target)
                        try:
                            self.load(package, try_relative_path=False)
                        except (ImportError, LoadingError) as error:
                            logger.debug("Could not follow alias %s: %s", member.path, error)
                            load_failures.add(package)
                except CyclicAliasError as error:
                    logger.debug(str(error))
                else:
                    logger.debug("Alias %s was resolved to %s", member.path, member.final_target.path)  # type: ignore[union-attr]
                    resolved.add(member.path)

            # Recurse into unseen modules and classes.
            elif member.kind in {Kind.MODULE, Kind.CLASS} and member.path not in seen:
                sub_resolved, sub_unresolved = self.resolve_module_aliases(
                    member,
                    implicit=implicit,
                    external=external,
                    seen=seen,
                    load_failures=load_failures,
                )
                resolved |= sub_resolved
                unresolved |= sub_unresolved

        return resolved, unresolved

    def stats(self) -> Stats:
        """Compute some statistics.

        Returns:
            Some statistics.
        """
        stats = Stats(self)
        stats.time_spent_visiting = self._time_stats["time_spent_visiting"]
        stats.time_spent_inspecting = self._time_stats["time_spent_inspecting"]
        return stats

    def _load_package(self, package: Package | NamespacePackage, *, submodules: bool = True) -> Module:
        top_module = self._load_module(package.name, package.path, submodules=submodules)
        self.modules_collection.set_member(top_module.path, top_module)
        if isinstance(package, NamespacePackage):
            return top_module
        if package.stubs:
            self.expand_wildcards(top_module)
            # If stubs are in the package itself, they have been merged while loading modules,
            # so only the top-level init module needs to be merged still.
            # If stubs are in another package (a stubs-only package),
            # then we need to load the entire stubs package to merge everything.
            submodules = submodules and package.stubs.parent != package.path.parent
            stubs = self._load_module(package.name, package.stubs, submodules=submodules)
            return merge_stubs(top_module, stubs)
        return top_module

    def _load_module(
        self,
        module_name: str,
        module_path: Path | list[Path],
        *,
        submodules: bool = True,
        parent: Module | None = None,
    ) -> Module:
        try:
            return self._load_module_path(module_name, module_path, submodules=submodules, parent=parent)
        except SyntaxError as error:
            raise LoadingError(f"Syntax error: {error}") from error
        except ImportError as error:
            raise LoadingError(f"Import error: {error}") from error
        except UnicodeDecodeError as error:
            raise LoadingError(f"UnicodeDecodeError when loading {module_path}: {error}") from error
        except OSError as error:
            raise LoadingError(f"OSError when loading {module_path}: {error}") from error

    def _load_module_path(
        self,
        module_name: str,
        module_path: Path | list[Path],
        *,
        submodules: bool = True,
        parent: Module | None = None,
    ) -> Module:
        logger.debug("Loading path %s", module_path)
        if isinstance(module_path, list):
            module = self._create_module(module_name, module_path)
        elif self.force_inspection:
            module = self._inspect_module(module_name, module_path, parent)
        elif module_path.suffix in {".py", ".pyi"}:
            module = self._visit_module(module_name, module_path, parent)
        elif self.allow_inspection:
            module = self._inspect_module(module_name, module_path, parent)
        else:
            raise LoadingError("Cannot load compiled module without inspection")
        if submodules:
            self._load_submodules(module)
        return module

    def _load_submodules(self, module: Module) -> None:
        for subparts, subpath in self.finder.submodules(module):
            self._load_submodule(module, subparts, subpath)

    def _load_submodule(self, module: Module, subparts: tuple[str, ...], subpath: Path) -> None:
        for subpart in subparts:
            if "." in subpart:
                logger.debug("Skip %s, dots in filenames are not supported", subpath)
                return
        try:
            parent_module = self._get_or_create_parent_module(module, subparts, subpath)
        except UnimportableModuleError as error:
            # NOTE: Why don't we load submodules when there's no init module in their folder?
            # Usually when a folder with Python files does not have an __init__.py module,
            # it's because the Python files are scripts that should never be imported.
            # Django has manage.py somewhere for example, in a folder without init module.
            # This script isn't part of the Python API, as it's meant to be called on the CLI exclusively
            # (at least it was the case a few years ago when I was still using Django).

            # The other case when there's no init module is when a package is a native namespace package (PEP 420).
            # It does not make sense to have a native namespace package inside of a regular package (having init modules above),
            # because the regular package above blocks the namespace feature from happening, so I consider it a user error.
            # It's true that users could have a native namespace package inside of a pkg_resources-style namespace package,
            # but I've never seen this happen.

            # It's also true that Python can actually import the module under the (wrongly declared) native namespace package,
            # so the Griffe debug log message is a bit misleading,
            # but that's because in that case Python acts like the whole tree is a regular package.
            # It works when the namespace package appears in only one search path (`sys.path`),
            # but will fail if it appears in multiple search paths: Python will only find the first occurrence.
            # It's better to not falsely support this, and to warn users.
            logger.debug("%s. Missing __init__ module?", error)
            return
        submodule_name = subparts[-1]
        try:
            submodule = self._load_module(
                submodule_name,
                subpath,
                submodules=False,
                parent=parent_module,
            )
        except LoadingError as error:
            logger.debug(str(error))
        else:
            if submodule_name in parent_module.members:
                member = parent_module.members[submodule_name]
                if member.is_alias or not member.is_module:
                    logger.debug(
                        "Submodule '%s' is shadowing the member at the same path. "
                        "We recommend renaming the member or the submodule (for example prefixing it with `_`), "
                        "see https://mkdocstrings.github.io/griffe/best_practices/#avoid-member-submodule-name-shadowing.",
                        submodule.path,
                    )
            parent_module.set_member(submodule_name, submodule)

    def _create_module(self, module_name: str, module_path: Path | list[Path]) -> Module:
        return Module(
            module_name,
            filepath=module_path,
            lines_collection=self.lines_collection,
            modules_collection=self.modules_collection,
        )

    def _visit_module(self, module_name: str, module_path: Path, parent: Module | None = None) -> Module:
        code = module_path.read_text(encoding="utf8")
        if self.store_source:
            self.lines_collection[module_path] = code.splitlines(keepends=False)
        start = datetime.now(tz=timezone.utc)
        module = visit(
            module_name,
            filepath=module_path,
            code=code,
            extensions=self.extensions,
            parent=parent,
            docstring_parser=self.docstring_parser,
            docstring_options=self.docstring_options,
            lines_collection=self.lines_collection,
            modules_collection=self.modules_collection,
        )
        elapsed = datetime.now(tz=timezone.utc) - start
        self._time_stats["time_spent_visiting"] += elapsed.microseconds
        return module

    def _inspect_module(self, module_name: str, filepath: Path | None = None, parent: Module | None = None) -> Module:
        for prefix in self.ignored_modules:
            if module_name.startswith(prefix):
                raise ImportError(f"Ignored module '{module_name}'")
        if self.store_source and filepath and filepath.suffix in {".py", ".pyi"}:
            self.lines_collection[filepath] = filepath.read_text(encoding="utf8").splitlines(keepends=False)
        start = datetime.now(tz=timezone.utc)
        try:
            module = inspect(
                module_name,
                filepath=filepath,
                import_paths=self.finder.search_paths,
                extensions=self.extensions,
                parent=parent,
                docstring_parser=self.docstring_parser,
                docstring_options=self.docstring_options,
                lines_collection=self.lines_collection,
                modules_collection=self.modules_collection,
            )
        except SystemExit as error:
            raise ImportError(f"Importing '{module_name}' raised a system exit") from error
        elapsed = datetime.now(tz=timezone.utc) - start
        self._time_stats["time_spent_inspecting"] += elapsed.microseconds
        return module

    def _get_or_create_parent_module(
        self,
        module: Module,
        subparts: tuple[str, ...],
        subpath: Path,
    ) -> Module:
        parent_parts = subparts[:-1]
        if not parent_parts:
            return module
        parent_module = module
        parents = list(subpath.parents)
        if subpath.stem == "__init__":
            parents.pop(0)
        for parent_offset, parent_part in enumerate(parent_parts, 2):
            module_filepath = parents[len(subparts) - parent_offset]
            try:
                parent_module = parent_module.get_member(parent_part)
            except KeyError as error:
                if parent_module.is_namespace_package or parent_module.is_namespace_subpackage:
                    next_parent_module = self._create_module(parent_part, [module_filepath])
                    parent_module.set_member(parent_part, next_parent_module)
                    parent_module = next_parent_module
                else:
                    raise UnimportableModuleError(f"Skip {subpath}, it is not importable") from error
            else:
                parent_namespace = parent_module.is_namespace_package or parent_module.is_namespace_subpackage
                if parent_namespace and module_filepath not in parent_module.filepath:  # type: ignore[operator]
                    parent_module.filepath.append(module_filepath)  # type: ignore[union-attr]
        return parent_module

    def _expand_wildcard(self, wildcard_obj: Alias) -> list[tuple[Object | Alias, int | None, int | None]]:
        module = self.modules_collection.get_member(wildcard_obj.wildcard)  # type: ignore[arg-type]  # we know it's a wildcard
        return [
            (imported_member, wildcard_obj.alias_lineno, wildcard_obj.alias_endlineno)
            for imported_member in module.members.values()
            if imported_member.is_wildcard_exposed
        ]


def load(
    objspec: str | Path | None = None,
    /,
    *,
    submodules: bool = True,
    try_relative_path: bool = True,
    extensions: Extensions | None = None,
    search_paths: Sequence[str | Path] | None = None,
    docstring_parser: DocstringStyle | Parser | None = None,
    docstring_options: dict[str, Any] | None = None,
    lines_collection: LinesCollection | None = None,
    modules_collection: ModulesCollection | None = None,
    allow_inspection: bool = True,
    force_inspection: bool = False,
    store_source: bool = True,
    find_stubs_package: bool = False,
    resolve_aliases: bool = False,
    resolve_external: bool | None = None,
    resolve_implicit: bool = False,
) -> Object | Alias:
    """Load and return a Griffe object.

    In Griffe's context, loading means:

    - searching for a package, and finding it on the file system or as a builtin module
        (see the [`ModuleFinder`][griffe.ModuleFinder] class for more information)
    - extracting information from each of its (sub)modules, by either parsing
        the source code (see the [`visit`][griffe.visit] function)
        or inspecting the module at runtime (see the [`inspect`][griffe.inspect] function)

    The extracted information is stored in a collection of modules, which can be queried later.
    Each collected module is a tree of objects, representing the structure of the module.
    See the [`Module`][griffe.Module], [`Class`][griffe.Class],
    [`Function`][griffe.Function], and [`Attribute`][griffe.Attribute] classes
    for more information.

    The main class used to load modules is [`GriffeLoader`][griffe.GriffeLoader].
    Convenience functions like this one and [`load_git`][griffe.load_git] are also available.

    Example:
        ```python
        import griffe

        module = griffe.load(...)
        ```

        This is a shortcut for:

        ```python
        from griffe import GriffeLoader

        loader = GriffeLoader(...)
        module = loader.load(...)
        ```

        See the documentation for the loader: [`GriffeLoader`][griffe.GriffeLoader].

    Parameters:
        objspec: The Python path of an object, or file path to a module.
        submodules: Whether to recurse on the submodules.
            This parameter only makes sense when loading a package (top-level module).
        try_relative_path: Whether to try finding the module as a relative path.
        extensions: The extensions to use.
        search_paths: The paths to search into.
        docstring_parser: The docstring parser to use. By default, no parsing is done.
        docstring_options: Additional docstring parsing options.
        lines_collection: A collection of source code lines.
        modules_collection: A collection of modules.
        allow_inspection: Whether to allow inspecting modules when visiting them is not possible.
        force_inspection: Whether to force using dynamic analysis when loading data.
        store_source: Whether to store code source in the lines collection.
        find_stubs_package: Whether to search for stubs-only package.
            If both the package and its stubs are found, they'll be merged together.
            If only the stubs are found, they'll be used as the package itself.
        resolve_aliases: Whether to resolve aliases.
        resolve_external: Whether to try to load unspecified modules to resolve aliases.
            Default value (`None`) means to load external modules only if they are the private sibling
            or the origin module (for example when `ast` imports from `_ast`).
        resolve_implicit: When false, only try to resolve an alias if it is explicitly exported.

    Returns:
        A Griffe object.
    """
    loader = GriffeLoader(
        extensions=extensions,
        search_paths=search_paths,
        docstring_parser=docstring_parser,
        docstring_options=docstring_options,
        lines_collection=lines_collection,
        modules_collection=modules_collection,
        allow_inspection=allow_inspection,
        force_inspection=force_inspection,
        store_source=store_source,
    )
    result = loader.load(
        objspec,
        submodules=submodules,
        try_relative_path=try_relative_path,
        find_stubs_package=find_stubs_package,
    )
    if resolve_aliases:
        loader.resolve_aliases(implicit=resolve_implicit, external=resolve_external)
    return result


def load_git(
    objspec: str | Path | None = None,
    /,
    *,
    ref: str = "HEAD",
    repo: str | Path = ".",
    submodules: bool = True,
    extensions: Extensions | None = None,
    search_paths: Sequence[str | Path] | None = None,
    docstring_parser: DocstringStyle | Parser | None = None,
    docstring_options: dict[str, Any] | None = None,
    lines_collection: LinesCollection | None = None,
    modules_collection: ModulesCollection | None = None,
    allow_inspection: bool = True,
    force_inspection: bool = False,
    find_stubs_package: bool = False,
    resolve_aliases: bool = False,
    resolve_external: bool | None = None,
    resolve_implicit: bool = False,
) -> Object | Alias:
    """Load and return a module from a specific Git reference.

    This function will create a temporary
    [git worktree](https://git-scm.com/docs/git-worktree) at the requested reference
    before loading `module` with [`griffe.load`][griffe.load].

    This function requires that the `git` executable is installed.

    Examples:
        ```python
        from griffe import load_git

        old_api = load_git("my_module", ref="v0.1.0", repo="path/to/repo")
        ```

    Parameters:
        objspec: The Python path of an object, or file path to a module.
        ref: A Git reference such as a commit, tag or branch.
        repo: Path to the repository (i.e. the directory *containing* the `.git` directory)
        submodules: Whether to recurse on the submodules.
            This parameter only makes sense when loading a package (top-level module).
        extensions: The extensions to use.
        search_paths: The paths to search into (relative to the repository root).
        docstring_parser: The docstring parser to use. By default, no parsing is done.
        docstring_options: Additional docstring parsing options.
        lines_collection: A collection of source code lines.
        modules_collection: A collection of modules.
        allow_inspection: Whether to allow inspecting modules when visiting them is not possible.
        force_inspection: Whether to force using dynamic analysis when loading data.
        find_stubs_package: Whether to search for stubs-only package.
            If both the package and its stubs are found, they'll be merged together.
            If only the stubs are found, they'll be used as the package itself.
        resolve_aliases: Whether to resolve aliases.
        resolve_external: Whether to try to load unspecified modules to resolve aliases.
            Default value (`None`) means to load external modules only if they are the private sibling
            or the origin module (for example when `ast` imports from `_ast`).
        resolve_implicit: When false, only try to resolve an alias if it is explicitly exported.

    Returns:
        A Griffe object.
    """
    with tmp_worktree(repo, ref) as worktree:
        search_paths = [worktree / path for path in search_paths or ["."]]
        if isinstance(objspec, Path):
            objspec = worktree / objspec

        return load(
            objspec,
            submodules=submodules,
            try_relative_path=False,
            extensions=extensions,
            search_paths=search_paths,
            docstring_parser=docstring_parser,
            docstring_options=docstring_options,
            lines_collection=lines_collection,
            modules_collection=modules_collection,
            allow_inspection=allow_inspection,
            force_inspection=force_inspection,
            find_stubs_package=find_stubs_package,
            resolve_aliases=resolve_aliases,
            resolve_external=resolve_external,
            resolve_implicit=resolve_implicit,
        )


def load_pypi(
    package: str,  # noqa: ARG001
    distribution: str,  # noqa: ARG001
    version_spec: str,  # noqa: ARG001
    *,
    submodules: bool = True,  # noqa: ARG001
    extensions: Extensions | None = None,  # noqa: ARG001
    search_paths: Sequence[str | Path] | None = None,  # noqa: ARG001
    docstring_parser: DocstringStyle | Parser | None = None,  # noqa: ARG001
    docstring_options: dict[str, Any] | None = None,  # noqa: ARG001
    lines_collection: LinesCollection | None = None,  # noqa: ARG001
    modules_collection: ModulesCollection | None = None,  # noqa: ARG001
    allow_inspection: bool = True,  # noqa: ARG001
    force_inspection: bool = False,  # noqa: ARG001
    find_stubs_package: bool = False,  # noqa: ARG001
) -> Object | Alias:
    """Load and return a module from a specific package version downloaded using pip.

    [:octicons-heart-fill-24:{ .pulse } Sponsors only](../../insiders/index.md){ .insiders } &mdash;
    [:octicons-tag-24: Insiders 1.1.0](../../insiders/changelog.md#1.1.0).

    Parameters:
        package: The package import name.
        distribution: The distribution name.
        version_spec: The version specifier to use when installing with pip.
        submodules: Whether to recurse on the submodules.
            This parameter only makes sense when loading a package (top-level module).
        extensions: The extensions to use.
        search_paths: The paths to search into (relative to the repository root).
        docstring_parser: The docstring parser to use. By default, no parsing is done.
        docstring_options: Additional docstring parsing options.
        lines_collection: A collection of source code lines.
        modules_collection: A collection of modules.
        allow_inspection: Whether to allow inspecting modules when visiting them is not possible.
        force_inspection: Whether to force using dynamic analysis when loading data.
        find_stubs_package: Whether to search for stubs-only package.
            If both the package and its stubs are found, they'll be merged together.
            If only the stubs are found, they'll be used as the package itself.
    """
    raise ValueError("Not available in non-Insiders versions of Griffe")
