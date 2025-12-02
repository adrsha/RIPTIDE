#!/usr/bin/env python3
"""
Rust Code Hierarchy Generator
Generates an interactive Treant.js visualization of Rust project structure
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class NodeType(Enum):
    FUNCTION    = "function"
    STRUCT      = "struct"
    ENUM        = "enum"
    TRAIT       = "trait"
    IMPL        = "impl"
    MODULE      = "module"
    TYPE_ALIAS  = "type_alias"
    CONST       = "const"
    TRAIT_IMPL  = "trait_impl"

@dataclass
class Field:
    name:           str
    type_name:      str
    is_public:      bool = True
    is_fn_pointer:  bool = False
    fn_pointer_sig: str  = ""

@dataclass
class TraitMethod:
    name:        str
    params:      List[Field]
    return_type: str
    has_default: bool = False


@dataclass
class Method:
    name:        str
    params:      List[Field]
    return_type: str
    is_public:   bool = True

@dataclass
class EnumVariant:
    name:   str
    fields: List[Field]

@dataclass
class Node:
    id:            str
    name:          str
    node_type:     NodeType
    file_path:     str
    is_public:     bool        = True
    is_used:       bool        = False
    fields:        List[Field] = field(default_factory=list)
    methods:       List[Method] = field(default_factory=list)
    params:        List[Field] = field(default_factory=list)
    return_type:   str         = ""
    variants:      List[EnumVariant] = field(default_factory=list)
    linked_types:  Set[str]    = field(default_factory=set)
    full_path:     str         = ""
    children:      List['Node'] = field(default_factory=list)
    trait_methods: List[TraitMethod] = field(default_factory=list)
    impl_trait:    str         = "" 
    impl_for:      str         = ""
    dependents:    List['Node'] = field(default_factory=list)

class RustParser:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.nodes:       Dict[str, Node] = {}
        self.std_types:   Set[str]        = {
            'String', 'Vec', 'Option', 'Result', 'Box', 'Rc', 'Arc',
            'HashMap', 'HashSet', 'BTreeMap', 'BTreeSet', 'LinkedList',
            'i8', 'i16', 'i32', 'i64', 'i128', 'isize',
            'u8', 'u16', 'u32', 'u64', 'u128', 'usize',
            'f32', 'f64', 'bool', 'char', 'str', '()', 'Self'
        }
        self.usage_map:   Dict[str, Set[str]] = {}
        self.use_imports: Dict[str, str]      = {}  # Maps simple name to full path

    def is_std_type(self, type_name: str) -> bool:
        """Check if a type is from standard library"""
        clean_type = self._clean_type_name(type_name)
        return clean_type in self.std_types

    def _clean_type_name(self, type_name: str) -> str:
        """Extract base type name from complex types, preserving module paths"""
        type_name = type_name.strip()
        type_name = re.sub(r'&(mut\s+)?', '', type_name)
        type_name = re.sub(r'<.*>', '', type_name)
        type_name = type_name.strip()
        
        # Remove leading 'crate::' or 'self::' or 'super::'
        type_name = re.sub(r'^(crate|self|super)::', '', type_name)
        
        return type_name

    def _extract_inner_types(self, type_name: str) -> List[str]:
        """Extract types from generics like Vec<T>, Option<Result<T, E>>"""
        types = []
        
        # Find the outermost angle brackets
        start_idx = type_name.find('<')
        if start_idx == -1:
            return types
        
        # Extract everything inside angle brackets, handling nesting
        depth   = 0
        current = ""
        
        for i in range(start_idx, len(type_name)):
            char = type_name[i]
            
            if char == '<':
                if depth > 0:
                    current += char
                depth += 1
            elif char == '>':
                depth -= 1
                if depth > 0:
                    current += char
                elif depth == 0:
                    # We've closed the outermost bracket
                    if current.strip():
                        types.append(current.strip())
                    break
            elif depth > 0:
                if char == ',' and depth == 1:
                    # Top-level comma separator
                    if current.strip():
                        types.append(current.strip())
                    current = ""
                else:
                    current += char
        
        # Recursively extract from nested types
        nested_types = []
        for t in types:
            nested_types.extend(self._extract_inner_types(t))
        types.extend(nested_types)
        
        return types


    def scan_project(self):
        """Scan all Rust files in the project, excluding target directory"""
        rust_files = []
        
        for rust_file in self.project_root.rglob("*.rs"):
            if 'target' in rust_file.parts:
                continue
            rust_files.append(rust_file)
        
        print(f"Found {len(rust_files)} Rust files (excluding target/)")
        
        for rust_file in rust_files:
            self._parse_file(rust_file)
        
        # Create function nodes from methods
        self._create_method_function_nodes()
        
        # Mark usage
        self._mark_usage()

    def _parse_file(self, file_path: Path):
        """Parse a single Rust file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return
        
        rel_path    = file_path.relative_to(self.project_root)
        module_path = str(rel_path.with_suffix('')).replace(os.sep, '::')
        
        # Parse use statements first
        self._parse_use_statements(content, module_path)
        
        # Parse structs
        self._parse_structs(content, str(rel_path), module_path)
        
        # Parse enums
        self._parse_enums(content, str(rel_path), module_path)
        
        # Parse traits
        self._parse_traits(content, str(rel_path), module_path)
        
        # Parse trait implementations
        self._parse_trait_impls(content, str(rel_path), module_path)
        
        # Parse type aliases
        self._parse_type_aliases(content, str(rel_path), module_path)
        
        # Parse constants
        self._parse_constants(content, str(rel_path), module_path)
        
        # Parse functions
        self._parse_functions(content, str(rel_path), module_path)

    def _parse_use_statements(self, content: str, current_module: str):
        """Parse use statements to build import map"""
        use_pattern = r'use\s+(?:crate::)?([^;]+);'
        
        for match in re.finditer(use_pattern, content):
            use_path = match.group(1).strip()
            
            # Handle use statements like:
            # use client::Client;
            # use client::{Client, Server};
            # use client::Client as C;
            
            # Skip wildcard imports
            if '*' in use_path:
                continue
            
            # Handle braced imports
            if '{' in use_path:
                base_path = use_path.split('{')[0].strip().rstrip('::')
                items     = use_path.split('{')[1].split('}')[0]
                
                for item in items.split(','):
                    item = item.strip()
                    if not item:
                        continue
                    
                    # Handle 'as' aliases
                    if ' as ' in item:
                        original, alias = item.split(' as ')
                        simple_name     = alias.strip()
                        full_path       = f"{base_path}::{original.strip()}"
                    else:
                        simple_name = item
                        full_path   = f"{base_path}::{item}"
                    
                    self.use_imports[simple_name] = full_path
            else:
                # Simple import like 'use client::Client;'
                parts = use_path.split('::')
                
                # Handle 'as' aliases
                if ' as ' in use_path:
                    path_part, alias = use_path.split(' as ')
                    simple_name      = alias.strip()
                    full_path        = path_part.strip()
                else:
                    simple_name = parts[-1]
                    full_path   = use_path
                
                self.use_imports[simple_name] = full_path

    def _resolve_type_path(self, type_name: str) -> List[str]:
        """
        Resolve a type name to possible full paths.
        Returns a list of candidate paths to search for.
        """
        candidates = []
        
        # If it's already a qualified path like 'client::Client'
        if '::' in type_name:
            candidates.append(type_name)
            # Also try with each segment as the base
            parts = type_name.split('::')
            for i in range(len(parts)):
                candidates.append('::'.join(parts[i:]))
        else:
            # Simple type name - check use imports
            if type_name in self.use_imports:
                candidates.append(self.use_imports[type_name])
            
            # Always add the simple name itself as a candidate
            candidates.append(type_name)
        
        return candidates

    def _find_node_by_type(self, type_name: str) -> Optional[Node]:
        """
        Find a node by resolving the type name to its full path.
        Handles both simple names and qualified paths.
        """
        candidates = self._resolve_type_path(type_name)
        
        for candidate in candidates:
            # Try exact full path match first
            for node in self.nodes.values():
                if node.full_path.endswith(candidate):
                    return node
            
            # Try matching just the name part
            simple_candidate = candidate.split('::')[-1]
            for node in self.nodes.values():
                if node.name == simple_candidate:
                    # Verify the path is compatible if candidate has path
                    if '::' in candidate:
                        path_parts = candidate.split('::')
                        if len(path_parts) > 1:
                            # Check if node's path ends with the candidate path
                            node_parts = node.full_path.split('::')
                            if len(node_parts) >= len(path_parts):
                                if node_parts[-len(path_parts):] == path_parts:
                                    return node
                    else:
                        return node
        
        return None

    def _extract_fn_references_from_signature(self, signature: str) -> List[str]:
        """Extract function references from function pointer signatures"""
        refs = []

        # Pattern for explicit function paths like def_fns::update::default
        fn_path_pattern = r'([\w:]+::\w+)'

        for match in re.finditer(fn_path_pattern, signature):
            path = match.group(1)
            # Only add if it looks like a function path (has ::)
            if '::' in path:
                refs.append(path)

        return refs

    def _parse_structs(self, content: str, file_path: str, module_path: str):
        """Parse struct definitions"""
        struct_pattern = r'(?:pub\s+)?struct\s+(\w+)\s*(?:<[^>]+>)?\s*\{'
        
        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)
            is_public   = 'pub' in content[max(0, match.start()-10):match.start()]

            start = match.end()
            depth = 1
            end   = start

            for i in range(start, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            
            body    = content[start:end]
            fields  = self._parse_fields(body)
            node_id = f"{module_path}::{struct_name}"
            
            node = Node(
                id        = node_id,
                name      = struct_name,
                node_type = NodeType.STRUCT,
                file_path = file_path,
                is_public = is_public,
                fields    = fields,
                full_path = node_id
            )

            for field in fields:
                if field.is_fn_pointer:
                    fn_refs = self._extract_fn_references_from_signature(field.fn_pointer_sig)
                    for fn_ref in fn_refs:
                        clean_ref = self._clean_type_name(fn_ref)
                        if not self.is_std_type(clean_ref):
                            node.linked_types.add(f"{field.name}::{clean_ref}")
                else:
                    clean_type = self._clean_type_name(field.type_name)
                    if not self.is_std_type(clean_type):
                        node.linked_types.add(clean_type)

                    inner_types = self._extract_inner_types(field.type_name)
                    for inner in inner_types:
                        clean_inner = self._clean_type_name(inner)
                        if not self.is_std_type(clean_inner):
                            node.linked_types.add(clean_inner)

            self.nodes[node_id] = node
            
            # Parse impl blocks and track function references
            self._parse_impl_blocks(content, struct_name, node, file_path, module_path)
            
            # Track function references in impl blocks
            self._track_function_references(content, struct_name, node)

    def _parse_fields(self, body: str) -> List[Field]:
        """Parse struct fields"""
        fields        = []
        field_pattern = r'(?:pub\s+)?(\w+)\s*:\s*([^,}]+)'

        for match in re.finditer(field_pattern, body):
            field_name = match.group(1)
            type_name  = match.group(2).strip()
            is_public  = 'pub' in body[max(0, match.start()-10):match.start()]

            is_fn_ptr = False
            fn_sig    = ""

            if 'fn' in type_name.lower() or 'Fn' in type_name:
                is_fn_ptr = True
                fn_sig    = type_name

            fields.append(Field(
                name           = field_name,
                type_name      = type_name,
                is_public      = is_public,
                is_fn_pointer  = is_fn_ptr,
                fn_pointer_sig = fn_sig
            ))
        
        return fields

    def _parse_impl_blocks(self, content: str, struct_name: str, node: Node, 
                          file_path: str, module_path: str):
        """Parse impl blocks for methods"""
        impl_pattern = rf'impl(?:\s+<[^>]+>)?\s+{struct_name}\s*(?:<[^>]+>)?\s*\{{'
        
        for match in re.finditer(impl_pattern, content):
            start = match.end()
            depth = 1
            end   = start
            
            for i in range(start, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            
            impl_body = content[start:end]
            methods   = self._parse_methods(impl_body)
            
            node.methods.extend(methods)
            
            # Track linked types from methods
            for method in methods:
                for param in method.params:
                    clean_type = self._clean_type_name(param.type_name)
                    if not self.is_std_type(clean_type):
                        node.linked_types.add(clean_type)
                    
                    inner_types = self._extract_inner_types(param.type_name)
                    for inner in inner_types:
                        clean_inner = self._clean_type_name(inner)
                        if not self.is_std_type(clean_inner):
                            node.linked_types.add(clean_inner)
                
                if method.return_type:
                    clean_ret = self._clean_type_name(method.return_type)
                    if not self.is_std_type(clean_ret):
                        node.linked_types.add(clean_ret)
                    
                    inner_types = self._extract_inner_types(method.return_type)
                    for inner in inner_types:
                        clean_inner = self._clean_type_name(inner)
                        if not self.is_std_type(clean_inner):
                            node.linked_types.add(clean_inner)

    def _track_function_references(self, content: str, struct_name: str, node: Node):
        """Track function references in impl blocks (e.g., def_fns::update::default)"""
        impl_pattern = rf'impl(?:\s+<[^>]+>)?\s+{struct_name}\s*(?:<[^>]+>)?\s*\{{'
        
        for match in re.finditer(impl_pattern, content):
            start = match.end()
            depth = 1
            end   = start
            
            for i in range(start, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            
            impl_body = content[start:end]
            
            # Look for function path references like def_fns::update::default
            fn_ref_pattern = r'([\w:]+)::([\w]+)'
            
            for fn_match in re.finditer(fn_ref_pattern, impl_body):
                full_path = fn_match.group(0)
                parts     = full_path.split('::')
                
                # Skip if it's just two parts (might be a type)
                if len(parts) >= 2:
                    # Extract the function name (last part)
                    fn_name = parts[-1]
                    # The module path is everything except the last part
                    module  = '::'.join(parts[:-1])
                    
                    # Add as a linked type so it gets tracked
                    node.linked_types.add(full_path)
                    node.linked_types.add(fn_name)

    def _parse_methods(self, impl_body: str) -> List[Method]:
        """Parse methods from impl block"""
        methods = [];
        # Updated pattern - don't require immediate { or ; after signature
        # This allows for whitespace and complex bodies
        method_pattern = r'(?:pub\s+)?(?:unsafe\s+)?(?:async\s+)?(?:const\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)\s*(?:->\s*([^{]+?))?(?=\s*\{)';
        
        for match in re.finditer(method_pattern, impl_body):
            method_name = match.group(1);
            params_str  = match.group(2);
            return_type = match.group(3).strip() if match.group(3) else "";
            is_public   = 'pub' in impl_body[max(0, match.start()-20):match.start()];
            
            params = self._parse_params(params_str);
            
            methods.append(Method(
                name        = method_name,
                params      = params,
                return_type = return_type,
                is_public   = is_public
            ));
        
        return methods;

    def _parse_params(self, params_str: str) -> List[Field]:
        """Parse function parameters"""
        params = []
        
        if not params_str.strip():
            return params
        
        # Split by comma but respect nested generics
        depth       = 0
        current     = ""
        param_parts = []
        
        for char in params_str:
            if char in '<([':
                depth += 1
            elif char in '>)]':
                depth -= 1
            elif char == ',' and depth == 0:
                if current.strip():
                    param_parts.append(current.strip())
                current = ""
                continue
            current += char
        
        if current.strip():
            param_parts.append(current.strip())
        
        for param in param_parts:
            param = param.strip()
            
            # Skip self parameters
            if param in ['self', '&self', '&mut self', 'mut self']:
                continue
            
            # Parse "name: type" pattern
            if ':' in param:
                parts      = param.split(':', 1)
                param_name = parts[0].strip()
                type_name  = parts[1].strip()
                
                params.append(Field(
                    name      = param_name,
                    type_name = type_name,
                    is_public = True
                ))
        
        return params

    def _parse_enums(self, content: str, file_path: str, module_path: str):
        """Parse enum definitions"""
        enum_pattern = r'(?:pub\s+)?enum\s+(\w+)\s*(?:<[^>]+>)?\s*\{'
        
        for match in re.finditer(enum_pattern, content):
            enum_name = match.group(1)
            is_public = 'pub' in content[max(0, match.start()-10):match.start()]
            
            start = match.end()
            depth = 1
            end   = start
            
            for i in range(start, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            
            body     = content[start:end]
            variants = self._parse_enum_variants(body)
            node_id  = f"{module_path}::{enum_name}"
            
            node = Node(
                id        = node_id,
                name      = enum_name,
                node_type = NodeType.ENUM,
                file_path = file_path,
                is_public = is_public,
                variants  = variants,
                full_path = node_id
            )
            
            # Track linked types from variants
            for variant in variants:
                for field in variant.fields:
                    clean_type = self._clean_type_name(field.type_name)
                    if not self.is_std_type(clean_type):
                        node.linked_types.add(clean_type)
                    
                    inner_types = self._extract_inner_types(field.type_name)
                    for inner in inner_types:
                        clean_inner = self._clean_type_name(inner)
                        if not self.is_std_type(clean_inner):
                            node.linked_types.add(clean_inner)
            
            self.nodes[node_id] = node

    def _create_method_function_nodes(self):
        """Create separate function nodes for all methods in structs/enums/traits"""
        new_nodes = {}
        
        for node in list(self.nodes.values()):
            if node.node_type in [NodeType.STRUCT, NodeType.ENUM, NodeType.TRAIT]:
                for method in node.methods:
                    # Create a unique function node for this method
                    fn_node_id = f"{node.full_path}::fn::{method.name}"
                    
                    fn_node = Node(
                        id          = fn_node_id,
                        name        = f"{node.name}::{method.name}",
                        node_type   = NodeType.FUNCTION,
                        file_path   = node.file_path,
                        is_public   = method.is_public,
                        params      = method.params,
                        return_type = method.return_type,
                        full_path   = fn_node_id
                    )
                    
                    # Track linked types from method parameters
                    for param in method.params:
                        clean_type = self._clean_type_name(param.type_name)
                        if not self.is_std_type(clean_type):
                            fn_node.linked_types.add(clean_type)
                        
                        inner_types = self._extract_inner_types(param.type_name)
                        for inner in inner_types:
                            clean_inner = self._clean_type_name(inner)
                            if not self.is_std_type(clean_inner):
                                fn_node.linked_types.add(clean_inner)
                    
                    # Track linked types from return type
                    if method.return_type:
                        clean_ret = self._clean_type_name(method.return_type)
                        if not self.is_std_type(clean_ret):
                            fn_node.linked_types.add(clean_ret)
                        
                        inner_types = self._extract_inner_types(method.return_type)
                        for inner in inner_types:
                            clean_inner = self._clean_type_name(inner)
                            if not self.is_std_type(clean_inner):
                                fn_node.linked_types.add(clean_inner)
                    
                    new_nodes[fn_node_id] = fn_node
        
        # Add all new function nodes to the main nodes dict
        self.nodes.update(new_nodes)

    def _parse_trait_impls(self, content: str, file_path: str, module_path: str):
        """Parse trait implementations (impl Trait for Type)"""
        impl_pattern = r'impl(?:\s+<[^>]+>)?\s+([\w:]+(?:<[^>]+>)?)\s+for\s+([\w:]+)(?:<[^>]+>)?\s*\{'
        
        for match in re.finditer(impl_pattern, content):
            trait_name = match.group(1).strip();
            type_name  = match.group(2).strip();
            
            start = match.end();
            depth = 1;
            end   = start;
            
            for i in range(start, len(content)):
                if content[i] == '{':
                    depth += 1;
                elif content[i] == '}':
                    depth -= 1;
                    if depth == 0:
                        end = i;
                        break;
            
            impl_body = content[start:end];
            methods   = self._parse_methods(impl_body);  # This already parses all methods correctly
            
            # Find the target type node and add methods to it
            target_node = self._find_node_by_type(type_name);
            if target_node:
                # Add all methods from trait impl to the target node
                # Mark that these methods are from a trait impl
                for method in methods:
                    method.is_public = True;  # Trait methods are always public
                target_node.methods.extend(methods);
                
                # Track the trait as a linked type
                clean_trait = self._clean_type_name(trait_name);
                if not self.is_std_type(clean_trait):
                    target_node.linked_types.add(clean_trait);
                    
                # Track linked types from methods
                for method in methods:
                    for param in method.params:
                        clean_param = self._clean_type_name(param.type_name);
                        if not self.is_std_type(clean_param):
                            target_node.linked_types.add(clean_param);
                        
                        inner_types = self._extract_inner_types(param.type_name);
                        for inner in inner_types:
                            clean_inner = self._clean_type_name(inner);
                            if not self.is_std_type(clean_inner):
                                target_node.linked_types.add(clean_inner);
                    
                    if method.return_type:
                        clean_ret = self._clean_type_name(method.return_type);
                        if not self.is_std_type(clean_ret):
                            target_node.linked_types.add(clean_ret);
                        
                        inner_types = self._extract_inner_types(method.return_type);
                        for inner in inner_types:
                            clean_inner = self._clean_type_name(inner);
                            if not self.is_std_type(clean_inner):
                                target_node.linked_types.add(clean_inner);
            else:
                # Create trait impl node only if target type not found
                node_id = f"{module_path}::impl_{trait_name}_for_{type_name}";
                
                node = Node(
                    id         = node_id,
                    name       = f"{trait_name} for {type_name}",
                    node_type  = NodeType.TRAIT_IMPL,
                    file_path  = file_path,
                    is_public  = True,
                    methods    = methods,
                    impl_trait = trait_name,
                    impl_for   = type_name,
                    full_path  = node_id
                );
                
                # Track linked types...
                clean_trait = self._clean_type_name(trait_name);
                clean_type  = self._clean_type_name(type_name);
                
                if not self.is_std_type(clean_trait):
                    node.linked_types.add(clean_trait);
                if not self.is_std_type(clean_type):
                    node.linked_types.add(clean_type);
                
                # Track linked types from methods
                for method in methods:
                    for param in method.params:
                        clean_param = self._clean_type_name(param.type_name);
                        if not self.is_std_type(clean_param):
                            node.linked_types.add(clean_param);
                        
                        inner_types = self._extract_inner_types(param.type_name);
                        for inner in inner_types:
                            clean_inner = self._clean_type_name(inner);
                            if not self.is_std_type(clean_inner):
                                node.linked_types.add(clean_inner);
                    
                    if method.return_type:
                        clean_ret = self._clean_type_name(method.return_type);
                        if not self.is_std_type(clean_ret):
                            node.linked_types.add(clean_ret);
                        
                        inner_types = self._extract_inner_types(method.return_type);
                        for inner in inner_types:
                            clean_inner = self._clean_type_name(inner);
                            if not self.is_std_type(clean_inner):
                                node.linked_types.add(clean_inner);
                
                self.nodes[node_id] = node;


    def _parse_trait_methods(self, trait_body: str) -> List[TraitMethod]:
        """Parse methods from trait definition"""
        methods        = []
        method_pattern = r'fn\s+(\w+)\s*(?:<[^>]+>)?\s*\(([^)]*)\)\s*(?:->\s*([^{;]+))?'
        
        for match in re.finditer(method_pattern, trait_body):
            method_name = match.group(1)
            params_str  = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else ""
            
            # Check if method has default implementation
            after_sig = trait_body[match.end():].lstrip()
            has_default = after_sig.startswith('{')
            
            params = self._parse_params(params_str)
            
            methods.append(TraitMethod(
                name        = method_name,
                params      = params,
                return_type = return_type,
                has_default = has_default
            ))
        
        return methods

    def _parse_traits(self, content: str, file_path: str, module_path: str):
        """Parse trait definitions"""
        trait_pattern = r'(?:pub\s+)?trait\s+(\w+)\s*(?:<[^>]+>)?\s*(?::\s*([^{]+))?\s*\{'
        
        for match in re.finditer(trait_pattern, content):
            trait_name = match.group(1)
            bounds     = match.group(2).strip() if match.group(2) else ""
            is_public  = 'pub' in content[max(0, match.start()-10):match.start()]
            
            start = match.end()
            depth = 1
            end   = start
            
            for i in range(start, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            
            body     = content[start:end]
            methods  = self._parse_trait_methods(body)
            node_id  = f"{module_path}::{trait_name}"
            
            node = Node(
                id            = node_id,
                name          = trait_name,
                node_type     = NodeType.TRAIT,
                file_path     = file_path,
                is_public     = is_public,
                trait_methods = methods,
                full_path     = node_id
            )
            
            # Track linked types from trait bounds
            if bounds:
                for bound in bounds.split('+'):
                    clean_bound = self._clean_type_name(bound.strip())
                    if not self.is_std_type(clean_bound):
                        node.linked_types.add(clean_bound)
            
            # Track linked types from methods
            for method in methods:
                for param in method.params:
                    clean_type = self._clean_type_name(param.type_name)
                    if not self.is_std_type(clean_type):
                        node.linked_types.add(clean_type)
                    
                    inner_types = self._extract_inner_types(param.type_name)
                    for inner in inner_types:
                        clean_inner = self._clean_type_name(inner)
                        if not self.is_std_type(clean_inner):
                            node.linked_types.add(clean_inner)
                
                if method.return_type:
                    clean_ret = self._clean_type_name(method.return_type)
                    if not self.is_std_type(clean_ret):
                        node.linked_types.add(clean_ret)
                    
                    inner_types = self._extract_inner_types(method.return_type)
                    for inner in inner_types:
                        clean_inner = self._clean_type_name(inner)
                        if not self.is_std_type(clean_inner):
                            node.linked_types.add(clean_inner)
            
            self.nodes[node_id] = node

    def _parse_enum_variants(self, body: str) -> List[EnumVariant]:
        """Parse enum variants"""
        variants        = []
        variant_pattern = r'(\w+)(?:\s*\(([^)]*)\)|\s*\{([^}]*)\})?'
        
        for match in re.finditer(variant_pattern, body):
            variant_name  = match.group(1)
            tuple_fields  = match.group(2)
            struct_fields = match.group(3)
            
            fields = []
            
            if tuple_fields:
                field_types = [f.strip() for f in tuple_fields.split(',') if f.strip()]
                for i, type_name in enumerate(field_types):
                    fields.append(Field(
                        name      = f"field_{i}",
                        type_name = type_name,
                        is_public = True
                    ))
            elif struct_fields:
                fields = self._parse_fields(struct_fields)
            
            variants.append(EnumVariant(
                name   = variant_name,
                fields = fields
            ))
        
        return variants

    def _parse_functions(self, content: str, file_path: str, module_path: str):
        """Parse standalone functions"""
        # Remove all impl blocks first to avoid parsing their methods as standalone functions
        cleaned_content = self._remove_impl_blocks(content)

        fn_pattern = r'(?:pub\s+)?fn\s+(\w+)\s*(?:<[^>]+>)?\s*\(([^)]*)\)\s*(?:->\s*([^{;]+))?'

        for match in re.finditer(fn_pattern, cleaned_content):
            fn_name     = match.group(1)
            params_str  = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else ""

            # Find the corresponding position in the original content
            original_pos = self._find_in_original(content, match.start(), match.group(0))
            if original_pos == -1:
                continue

            is_public = 'pub' in content[max(0, original_pos-10):original_pos]

            params  = self._parse_params(params_str)
            node_id = f"{module_path}::{fn_name}"

            node = Node(
                id          = node_id,
                name        = fn_name,
                node_type   = NodeType.FUNCTION,
                file_path   = file_path,
                is_public   = is_public,
                params      = params,
                return_type = return_type,
                full_path   = node_id
            )

            # Track linked types
            for param in params:
                clean_type = self._clean_type_name(param.type_name)
                if not self.is_std_type(clean_type):
                    node.linked_types.add(clean_type)

                inner_types = self._extract_inner_types(param.type_name)
                for inner in inner_types:
                    clean_inner = self._clean_type_name(inner)
                    if not self.is_std_type(clean_inner):
                        node.linked_types.add(clean_inner)

            if return_type:
                clean_ret = self._clean_type_name(return_type)
                if not self.is_std_type(clean_ret):
                    node.linked_types.add(clean_ret)

                inner_types = self._extract_inner_types(return_type)
                for inner in inner_types:
                    clean_inner = self._clean_type_name(inner)
                    if not self.is_std_type(clean_inner):
                        node.linked_types.add(clean_inner)

            self.nodes[node_id] = node

    def _parse_constants(self, content: str, file_path: str, module_path: str):
        """Parse constants"""
        const_pattern = r'(?:pub\s+)?const\s+(\w+)\s*:\s*([^=]+)='
        
        for match in re.finditer(const_pattern, content):
            const_name = match.group(1)
            const_type = match.group(2).strip()
            is_public  = 'pub' in content[max(0, match.start()-10):match.start()]
            node_id    = f"{module_path}::{const_name}"
            
            node = Node(
                id          = node_id,
                name        = const_name,
                node_type   = NodeType.CONST,
                file_path   = file_path,
                is_public   = is_public,
                return_type = const_type,  # Store type in return_type field
                full_path   = node_id
            )
            
            # Track the const type
            clean_type = self._clean_type_name(const_type)
            if not self.is_std_type(clean_type):
                node.linked_types.add(clean_type)
            
            inner_types = self._extract_inner_types(const_type)
            for inner in inner_types:
                clean_inner = self._clean_type_name(inner)
                if not self.is_std_type(clean_inner):
                    node.linked_types.add(clean_inner)
            
            self.nodes[node_id] = node

    def _parse_type_aliases(self, content: str, file_path: str, module_path: str):
        """Parse type aliases"""
        type_pattern = r'(?:pub\s+)?type\s+(\w+)\s*(?:<[^>]+>)?\s*=\s*([^;]+);'
        
        for match in re.finditer(type_pattern, content):
            alias_name = match.group(1)
            target_type = match.group(2).strip()
            is_public   = 'pub' in content[max(0, match.start()-10):match.start()]
            node_id     = f"{module_path}::{alias_name}"
            
            node = Node(
                id          = node_id,
                name        = alias_name,
                node_type   = NodeType.TYPE_ALIAS,
                file_path   = file_path,
                is_public   = is_public,
                return_type = target_type,  # Store target type in return_type field
                full_path   = node_id
            )
            
            # Track the target type
            clean_target = self._clean_type_name(target_type)
            if not self.is_std_type(clean_target):
                node.linked_types.add(clean_target)
            
            inner_types = self._extract_inner_types(target_type)
            for inner in inner_types:
                clean_inner = self._clean_type_name(inner)
                if not self.is_std_type(clean_inner):
                    node.linked_types.add(clean_inner)
            
            self.nodes[node_id] = node

    def _remove_impl_blocks(self, content: str) -> str:
        """Remove all impl blocks from content to avoid parsing their methods"""
        impl_pattern = r'impl(?:\s+<[^>]+>)?\s+(?:\w+(?:::\w+)*\s+for\s+)?(\w+)\s*(?:<[^>]+>)?\s*\{'
        
        result = []
        last_end = 0
        
        for match in re.finditer(impl_pattern, content):
            # Add content before this impl block
            result.append(content[last_end:match.start()])
            
            # Skip the impl block
            start = match.end()
            depth = 1
            
            for i in range(start, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        last_end = i + 1
                        break
        
        # Add remaining content
        result.append(content[last_end:])
        return ''.join(result)
    
    def _find_in_original(self, original: str, approx_pos: int, pattern: str) -> int:
        """Find the position of a pattern in the original content near an approximate position"""
        # Search within a reasonable range
        search_start = max(0, approx_pos - 100)
        search_end = min(len(original), approx_pos + 100)
        
        idx = original.find(pattern, search_start, search_end)
        return idx

    def _mark_usage(self):
        """Mark which nodes are used by others"""
        # Mark all public items as potentially used (they might be called from outside)
        for node in self.nodes.values():
            if node.is_public:
                node.is_used = True;
        
        # Mark items that are referenced internally
        for node in self.nodes.values():
            for linked_type in node.linked_types:
                target_node = self._find_node_by_type(linked_type);
                if target_node:
                    target_node.is_used = True;

    def _build_tree_structure(self) -> List[Dict]:
        """Build tree structure with parent-child relationships using resolved paths"""
        # First pass: build children relationships
        for node in self.nodes.values():
            for linked_type in node.linked_types:
                target_node = self._find_node_by_type(linked_type)
                if target_node and target_node not in node.children:
                    node.children.append(target_node)
                    # Also track reverse relationship (dependents)
                    if node not in target_node.dependents:
                        target_node.dependents.append(node)
        
        # Find root nodes (nodes not used as children)
        all_children = set()
        for node in self.nodes.values():
            for child in node.children:
                all_children.add(child.id)
        
        root_nodes = [node for node in self.nodes.values() if node.id not in all_children]
        
        return root_nodes

    def generate_output(self, output_dir: str = "output"):
        """Generate visualization files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Build graph data
        graph_data = self._build_graph_data()
        
        # Generate HTML with embedded data
        self._generate_html(output_path, graph_data)
        
        # Generate CSS
        self._generate_css(output_path)
        
        print(f"\nVisualization generated in '{output_dir}/' directory")
        print(f"Open '{output_dir}/index.html' in your browser")

    def _build_graph_data(self) -> Dict:
        """Build data structure for Cytoscape.js graph"""
        elements    = []
        added_nodes = set()
        added_edges = set()
        
        # Add all nodes
        for node in self.nodes.values():
            if node.id in added_nodes:
                continue
            
            added_nodes.add(node.id)
            html_parts = self._build_node_html(node)
            
            elements.append({
                'data': {
                    'id':        node.id,
                    'label':     node.name,
                    'type':      node.node_type.value,
                    'is_used':   node.is_used,
                    'html':      ''.join(html_parts),
                    'file_path': node.file_path
                },
                'classes': f"{node.node_type.value} {'unused' if not node.is_used else ''}"
            })
        
        # Add edges for type dependencies (struct/enum/trait -> other types they use)
        for node in self.nodes.values():
            if node.node_type in [NodeType.STRUCT, NodeType.ENUM, NodeType.TRAIT, NodeType.TYPE_ALIAS, NodeType.CONST]:
                for linked_type in node.linked_types:
                    target_node = self._find_node_by_type(linked_type)
                    if target_node and target_node.node_type in [NodeType.STRUCT, NodeType.ENUM, NodeType.TRAIT, NodeType.TYPE_ALIAS]:
                        edge_id = f"{node.id}-uses->{target_node.id}"
                        if edge_id not in added_edges:
                            added_edges.add(edge_id)
                            elements.append({
                                'data': {
                                    'id':        edge_id,
                                    'source':    node.id,
                                    'target':    target_node.id,
                                    'edgeType':  'uses'
                                },
                                'classes': 'edge-uses'
                            })
        
        # Add edges for method implementations (struct/enum/trait -> method functions)
        for node in self.nodes.values():
            if node.node_type in [NodeType.STRUCT, NodeType.ENUM, NodeType.TRAIT]:
                for method in node.methods:
                    # Find the corresponding function node we created
                    fn_node_id = f"{node.full_path}::fn::{method.name}"
                    if fn_node_id in self.nodes:
                        edge_id = f"{node.id}-has_method->{fn_node_id}"
                        if edge_id not in added_edges:
                            added_edges.add(edge_id)
                            elements.append({
                                'data': {
                                    'id':        edge_id,
                                    'source':    node.id,
                                    'target':    fn_node_id,
                                    'edgeType':  'has_method',
                                    'label':     'method'
                                },
                                'classes': 'edge-has-method'
                            })
        
        # Add edges from functions to types they use (function params/returns -> types)
        for node in self.nodes.values():
            if node.node_type == NodeType.FUNCTION:
                for linked_type in node.linked_types:
                    target_node = self._find_node_by_type(linked_type)
                    if target_node and target_node.node_type in [NodeType.STRUCT, NodeType.ENUM, NodeType.TRAIT]:
                        edge_id = f"{node.id}-uses->{target_node.id}"
                        if edge_id not in added_edges:
                            added_edges.add(edge_id)
                            elements.append({
                                'data': {
                                    'id':        edge_id,
                                    'source':    node.id,
                                    'target':    target_node.id,
                                    'edgeType':  'fn_uses_type'
                                },
                                'classes': 'edge-fn-uses-type'
                            })
        
        # Add edges for function pointers in struct fields
        for node in self.nodes.values():
            if node.node_type in [NodeType.STRUCT, NodeType.ENUM]:
                for field in node.fields:
                    if field.is_fn_pointer:
                        # Extract function references from the signature
                        fn_refs = self._extract_fn_references_from_signature(field.fn_pointer_sig)
                        for fn_ref in fn_refs:
                            fn_node = self._find_node_by_type(fn_ref)
                            if fn_node and fn_node.node_type == NodeType.FUNCTION:
                                edge_id = f"{node.id}-fn_ptr:{field.name}->{fn_node.id}"
                                if edge_id not in added_edges:
                                    added_edges.add(edge_id)
                                    elements.append({
                                        'data': {
                                            'id':        edge_id,
                                            'source':    node.id,
                                            'target':    fn_node.id,
                                            'edgeType':  'fn_pointer',
                                            'label':     f'fn_ptr: {field.name}'
                                        },
                                        'classes': 'edge-fn-pointer'
                                    })
        
        # Add edges for trait implementations
        for node in self.nodes.values():
            if node.node_type == NodeType.TRAIT_IMPL:
                # Connect trait impl to the trait
                if node.impl_trait:
                    trait_node = self._find_node_by_type(node.impl_trait)
                    if trait_node:
                        edge_id = f"{node.id}-impl_trait->{trait_node.id}"
                        if edge_id not in added_edges:
                            added_edges.add(edge_id)
                            elements.append({
                                'data': {
                                    'id':        edge_id,
                                    'source':    node.id,
                                    'target':    trait_node.id,
                                    'edgeType':  'impl_trait',
                                    'label':     'implements'
                                },
                                'classes': 'edge-impl-trait'
                            })
                
                # Connect type to trait impl
                if node.impl_for:
                    type_node = self._find_node_by_type(node.impl_for)
                    if type_node:
                        edge_id = f"{type_node.id}-has_impl->{node.id}"
                        if edge_id not in added_edges:
                            added_edges.add(edge_id)
                            elements.append({
                                'data': {
                                    'id':        edge_id,
                                    'source':    type_node.id,
                                    'target':    node.id,
                                    'edgeType':  'has_trait_impl',
                                    'label':     'impl for'
                                },
                                'classes': 'edge-has-trait-impl'
                            })
        
        return {
            'elements': elements,
            'style':    self._build_cytoscape_style()
        }

    def _find_method_function(self, parent_node: Node, method: Method) -> Optional[Node]:
        """
        Try to find a standalone function node that might correspond to this method.
        This is a heuristic - looks for functions with matching names in related modules.
        """
        # Look for functions with matching name
        method_path = f"{parent_node.full_path.rsplit('::', 1)[0]}::{method.name}"
        
        for node in self.nodes.values():
            if node.node_type == NodeType.FUNCTION:
                if node.full_path == method_path or node.name == method.name:
                    # Verify signature similarity
                    if len(node.params) == len(method.params):
                        return node
        
        return None

    def _build_node_html(self, node: Node) -> List[str]:
        """Build HTML content for a node (extracted for reuse)"""
        html_parts = [
            '<div class="node-content">',
            '<div class="node-header">',
            f'<div class="node-type-badge">{node.node_type.value}</div>',
            f'<div class="node-title">{node.name}</div>',
            '</div>'
        ]
        
        if node.return_type:
            html_parts.append(
                f'<div class="return-type-badge">'
                f'<span class="label">returns</span> {node.return_type}'
                f'</div>'
            )
        
        # Parameters
        if node.params:
            html_parts.extend([
                '<div class="section-wrapper">',
                '<div class="section-header">Parameters</div>',
                '<div class="params-list">'
            ])
            for param in node.params:
                html_parts.append(
                    f'<div class="param-item">'
                    f'<span class="param-name">{param.name}</span>'
                    f'<span class="param-sep">:</span>'
                    f'<span class="param-type">{param.type_name}</span>'
                    f'</div>'
                )
            html_parts.append('</div></div>')
        
        # Fields
        if node.fields:
            html_parts.extend([
                '<div class="section-wrapper">',
                '<div class="section-header">Fields</div>',
                '<div class="fields-preview">'
            ])
            for field in node.fields:
                vis      = '<span class="visibility">pub</span> ' if field.is_public else '<span class="visibility private">priv</span> '
                fn_badge = '<span class="fn-pointer-badge">fn ptr</span> ' if field.is_fn_pointer else ''
                html_parts.append(
                    f'<div class="field-item">'
                    f'{vis}{fn_badge}'
                    f'<span class="field-name">{field.name}</span>'
                    f'<span class="field-sep">:</span>'
                    f'<span class="field-type">{field.type_name}</span>'
                    f'</div>'
                )
            html_parts.append('</div></div>')
        
        # Methods
        if node.methods:
            html_parts.extend([
                '<div class="section-wrapper">',
                '<div class="section-header">Methods</div>',
                '<div class="methods-preview">'
            ])
            for method in node.methods:
                vis        = '<span class="visibility">pub</span> ' if method.is_public else '<span class="visibility private">priv</span> '
                param_list = ', '.join([f'{p.name}: {p.type_name}' for p in method.params])
                ret        = f' → {method.return_type}' if method.return_type else ''
                html_parts.append(
                    f'<div class="method-item">'
                    f'{vis}'
                    f'<span class="method-name">fn {method.name}</span>'
                    f'<span class="method-params">({param_list})</span>'
                    f'<span class="method-return">{ret}</span>'
                    f'</div>'
                )
            html_parts.append('</div></div>')
        
        # Trait methods
        if node.trait_methods:
            html_parts.extend([
                '<div class="section-wrapper">',
                '<div class="section-header">Trait Methods</div>',
                '<div class="methods-preview">'
            ])
            for method in node.trait_methods:
                param_list = ', '.join([f'{p.name}: {p.type_name}' for p in method.params])
                ret        = f' → {method.return_type}' if method.return_type else ''
                default    = '<span class="default-badge">default</span> ' if method.has_default else ''
                html_parts.append(
                    f'<div class="method-item">'
                    f'{default}'
                    f'<span class="method-name">fn {method.name}</span>'
                    f'<span class="method-params">({param_list})</span>'
                    f'<span class="method-return">{ret}</span>'
                    f'</div>'
                )
            html_parts.append('</div></div>')
        
        # Variants
        if node.variants:
            html_parts.extend([
                '<div class="section-wrapper">',
                '<div class="section-header">Variants</div>',
                '<div class="variants-list">'
            ])
            for variant in node.variants:
                if variant.fields:
                    field_list = ', '.join([f.type_name for f in variant.fields])
                    html_parts.append(
                        f'<div class="variant-item">'
                        f'<span class="variant-name">{variant.name}</span>'
                        f'<span class="variant-fields">({field_list})</span>'
                        f'</div>'
                    )
                else:
                    html_parts.append(f'<div class="variant-item"><span class="variant-name">{variant.name}</span></div>')
            html_parts.append('</div></div>')
        
        # Dependents
        if node.dependents:
            html_parts.extend([
                '<div class="section-wrapper">',
                '<div class="section-header">Used By</div>',
                '<div class="dependents-list">'
            ])
            for dependent in node.dependents[:10]:
                dep_type_badge = f'<span class="dep-type-badge {dependent.node_type.value}">{dependent.node_type.value}</span>'
                html_parts.append(
                    f'<div class="dependent-item">'
                    f'{dep_type_badge}'
                    f'<span class="dependent-name">{dependent.name}</span>'
                    f'</div>'
                )
            if len(node.dependents) > 10:
                html_parts.append(f'<div class="dependent-item more">+ {len(node.dependents) - 10} more...</div>')
            html_parts.append('</div></div>')
        
        html_parts.append(f'<div class="file-info"><span class="file-icon">📁</span> {node.file_path}</div>')
        html_parts.append('</div>')
        
        return html_parts

    def _build_cytoscape_style(self) -> List[Dict]:
        """Build Cytoscape.js style configuration"""
        return [
            {
                'selector': 'node',
                'style': {
                    'label':            'data(label)',
                    'text-valign':      'center',
                    'text-halign':      'center',
                    'background-color': '#1e293b',
                    'border-width':     2,
                    'border-color':     '#334155',
                    'width':            120,
                    'height':           60,
                    'font-size':        11,
                    'color':            '#f1f5f9',
                    'text-wrap':        'wrap',
                    'text-max-width':   100
                }
            },
            {'selector': 'node.struct',     'style': {'border-color': '#10b981', 'background-color': '#064e3b'}},
            {'selector': 'node.function',   'style': {'border-color': '#f59e0b', 'background-color': '#78350f', 'shape': 'round-rectangle'}},
            {'selector': 'node.enum',       'style': {'border-color': '#ef4444', 'background-color': '#7f1d1d'}},
            {'selector': 'node.trait',      'style': {'border-color': '#8b5cf6', 'background-color': '#5b21b6'}},
            {'selector': 'node.trait_impl', 'style': {'border-color': '#ec4899', 'background-color': '#831843'}},
            {'selector': 'node.type_alias', 'style': {'border-color': '#06b6d4', 'background-color': '#155e75'}},
            {'selector': 'node.const',      'style': {'border-color': '#a3e635', 'background-color': '#3f6212'}},
            {'selector': 'node.unused',     'style': {'opacity': 0.4}},
            {
                'selector': 'node.selected',
                'style': {
                    'border-width': 4,
                    'border-color': '#60a5fa'
                }
            },
            # Type uses type (struct uses another struct)
            {
                'selector': 'edge.edge-uses',
                'style': {
                    'width':              2,
                    'line-color':         '#60a5fa',
                    'target-arrow-color': '#60a5fa',
                    'target-arrow-shape': 'triangle',
                    'curve-style':        'bezier',
                    'opacity':            0.5
                }
            },
            # Struct/Enum/Trait has method
            {
                'selector': 'edge.edge-has-method',
                'style': {
                    'width':              3,
                    'line-color':         '#10b981',
                    'target-arrow-color': '#10b981',
                    'target-arrow-shape': 'vee',
                    'curve-style':        'bezier',
                    'opacity':            0.8,
                    'line-style':         'solid',
                    'label':              'data(label)',
                    'font-size':          9,
                    'color':              '#10b981',
                    'text-outline-color': '#000000',
                    'text-outline-width': 2
                }
            },
            # Function uses type (in params or return)
            {
                'selector': 'edge.edge-fn-uses-type',
                'style': {
                    'width':              2,
                    'line-color':         '#fbbf24',
                    'target-arrow-color': '#fbbf24',
                    'target-arrow-shape': 'triangle',
                    'curve-style':        'bezier',
                    'opacity':            0.6,
                    'line-style':         'dashed'
                }
            },
            # Function pointer field
            {
                'selector': 'edge.edge-fn-pointer',
                'style': {
                    'width':              3,
                    'line-color':         '#f59e0b',
                    'target-arrow-color': '#f59e0b',
                    'target-arrow-shape': 'diamond',
                    'curve-style':        'bezier',
                    'opacity':            0.9,
                    'line-style':         'dotted',
                    'label':              'data(label)',
                    'font-size':          9,
                    'color':              '#f59e0b',
                    'text-outline-color': '#000000',
                    'text-outline-width': 2
                }
            },
            # Trait impl implements trait
            {
                'selector': 'edge.edge-impl-trait',
                'style': {
                    'width':              3,
                    'line-color':         '#8b5cf6',
                    'target-arrow-color': '#8b5cf6',
                    'target-arrow-shape': 'triangle',
                    'curve-style':        'bezier',
                    'opacity':            0.8,
                    'line-style':         'solid',
                    'label':              'data(label)',
                    'font-size':          9,
                    'color':              '#8b5cf6',
                    'text-outline-color': '#000000',
                    'text-outline-width': 2
                }
            },
            # Type has trait impl
            {
                'selector': 'edge.edge-has-trait-impl',
                'style': {
                    'width':              2,
                    'line-color':         '#ec4899',
                    'target-arrow-color': '#ec4899',
                    'target-arrow-shape': 'vee',
                    'curve-style':        'bezier',
                    'opacity':            0.7,
                    'line-style':         'dashed',
                    'label':              'data(label)',
                    'font-size':          9,
                    'color':              '#ec4899',
                    'text-outline-color': '#000000',
                    'text-outline-width': 2
                }
            },
            {'selector': 'edge:selected', 'style': {'line-color': '#ffffff', 'target-arrow-color': '#ffffff', 'width': 4}}
        ]

    def _generate_html(self, output_path: Path, graph_data: Dict):
        """Generate HTML file with Cytoscape.js visualization"""
        graph_json = json.dumps(graph_data, indent=2)
        
        html_content = f'''<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rust Code Hierarchy</title>
        <link rel="stylesheet" href="styles.css">
        <script src="https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js"></script>
        <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
        <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
        <script src="https://unpkg.com/cytoscape-popper@2.0.0/cytoscape-popper.js"></script>
        <script src="https://unpkg.com/@popperjs/core@2.11.6/dist/umd/popper.min.js"></script>
    </head>
    <body>
        <div class="container">
            <h1>Rust Code Hierarchy Visualization</h1>
            <div class="controls">
                <button id="btn-fit">Fit to Screen</button>
                <button id="btn-vertical">Vertical Layout</button>
                <button id="btn-horizontal">Horizontal Layout</button>
                <button id="btn-circle">Circle Layout</button>
            </div>
            <div id="cy"></div>
            <div id="tooltip" class="node-tooltip"></div>
            <div class="legend">
                <div class="legend-title">Edge Types:</div>
                <div class="legend-items">
                    <div class="legend-item">
                        <div class="legend-line edge-uses-line"></div>
                        <span>Type uses Type</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-line edge-has-method-line"></div>
                        <span>Has Method</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-line edge-fn-uses-type-line"></div>
                        <span>Function uses Type</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-line edge-fn-pointer-line"></div>
                        <span>Function Pointer Field</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-line edge-impl-trait-line"></div>
                        <span>Implements Trait</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-line edge-has-trait-impl-line"></div>
                        <span>Has Trait Impl</span>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                const graphData = {graph_json};
                
                if (typeof cytoscape !== 'undefined' && typeof dagre !== 'undefined') {{
                    cytoscape.use(cytoscapeDagre);
                }}
                
                const cy = cytoscape({{
                    container:        document.getElementById('cy'),
                    elements:         graphData.elements,
                    style:            graphData.style,
                    layout:           {{ 
                        name:     'dagre', 
                        rankDir:  'TB', 
                        nodeSep:  50, 
                        rankSep:  100,
                        animate:  false
                    }},
                    wheelSensitivity: 0.2,
                    minZoom:          0.1,
                    maxZoom:          3
                }});
                
                const tooltip        = document.getElementById('tooltip');
                let selectedNode     = null;
                let tooltipPinned    = false;
                
                // Show tooltip on hover
                cy.on('mouseover', 'node', function(evt) {{
                    if (tooltipPinned) return;
                    
                    const node     = evt.target;
                    const position = node.renderedPosition();
                    
                    tooltip.innerHTML = node.data('html');
                    tooltip.style.display = 'block';
                    tooltip.style.left    = (position.x + 20) + 'px';
                    tooltip.style.top     = (position.y - 20) + 'px';
                }});
                
                // Hide tooltip on mouseout
                cy.on('mouseout', 'node', function(evt) {{
                    if (tooltipPinned) return;
                    tooltip.style.display = 'none';
                }});
                
                // Pin tooltip on click
                cy.on('tap', 'node', function(evt) {{
                    const node     = evt.target;
                    const position = node.renderedPosition();
                    
                    if (selectedNode === node && tooltipPinned) {{
                        // Unpin if clicking the same node
                        tooltipPinned = false;
                        tooltip.style.display = 'none';
                        selectedNode = null;
                        node.removeClass('selected');
                    }} else {{
                        // Pin to new node
                        if (selectedNode) {{
                            selectedNode.removeClass('selected');
                        }}
                        
                        tooltipPinned = true;
                        selectedNode  = node;
                        node.addClass('selected');
                        
                        tooltip.innerHTML = node.data('html');
                        tooltip.style.display = 'block';
                        tooltip.style.left    = (position.x + 20) + 'px';
                        tooltip.style.top     = (position.y - 20) + 'px';
                    }}
                }});
                
                // Close tooltip when clicking on background
                cy.on('tap', function(evt) {{
                    if (evt.target === cy) {{
                        tooltipPinned = false;
                        tooltip.style.display = 'none';
                        if (selectedNode) {{
                            selectedNode.removeClass('selected');
                            selectedNode = null;
                        }}
                    }}
                }});
                
                // Update tooltip position on pan/zoom
                cy.on('pan zoom', function() {{
                    if (tooltipPinned && selectedNode) {{
                        const position = selectedNode.renderedPosition();
                        tooltip.style.left = (position.x + 20) + 'px';
                        tooltip.style.top  = (position.y - 20) + 'px';
                    }}
                }});
                
                document.getElementById('btn-fit').addEventListener('click', function() {{
                    cy.fit();
                }});
                
                document.getElementById('btn-vertical').addEventListener('click', function() {{
                    cy.layout({{ 
                        name:              'dagre', 
                        rankDir:           'TB', 
                        nodeSep:           50, 
                        rankSep:           100,
                        animate:           true,
                        animationDuration: 500
                    }}).run();
                }});
                
                document.getElementById('btn-horizontal').addEventListener('click', function() {{
                    cy.layout({{ 
                        name:              'dagre', 
                        rankDir:           'LR', 
                        nodeSep:           50, 
                        rankSep:           100,
                        animate:           true,
                        animationDuration: 500
                    }}).run();
                }});
                
                document.getElementById('btn-circle').addEventListener('click', function() {{
                    cy.layout({{ 
                        name:              'circle',
                        animate:           true,
                        animationDuration: 500
                    }}).run();
                }});
                
                cy.fit();
            }});
        </script>
    </body>
    </html>'''
        
        with open(output_path / "index.html", 'w') as f:
            f.write(html_content)

    def _generate_css(self, output_path: Path):
        """Generate CSS file"""
        css_content = '''* {
        margin:     0;
        padding:    0;
        box-sizing: border-box;
    }

    body {
        font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background:  #000000;
        color:       #e4e4e7;
        min-height:  100vh;
        overflow:    hidden;
    }

    .container {
        width:          100vw;
        height:         100vh;
        display:        flex;
        flex-direction: column;
        position:       relative;
    }

    h1 {
        color:          #60a5fa;
        padding:        20px;
        font-size:      1.5rem;
        font-weight:    700;
        text-shadow:    0 0 20px rgba(96, 165, 250, 0.3);
        letter-spacing: -0.5px;
        background:     rgba(0, 0, 0, 0.5);
        border-bottom:  1px solid rgba(96, 165, 250, 0.2);
    }

    .controls {
        padding:       12px 20px;
        display:       flex;
        gap:           12px;
        background:    rgba(0, 0, 0, 0.5);
        border-bottom: 1px solid rgba(96, 165, 250, 0.2);
    }

    .controls button {
        background:    linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color:         white;
        border:        none;
        padding:       8px 16px;
        cursor:        pointer;
        border-radius: 6px;
        font-size:     13px;
        font-weight:   600;
        transition:    all 0.3s ease;
        box-shadow:    0 2px 4px rgba(0, 0, 0, 0.3);
    }

    .controls button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        transform:  translateY(-1px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
    }

    #cy {
        flex:       1;
        width:      100%;
        background: radial-gradient(circle at center, #0a0a0a 0%, #000000 100%);
    }

    /* Tooltip container */
    .node-tooltip {
        position:      absolute;
        display:       none;
        z-index:       10000;
        pointer-events: none;
        max-height:    80vh;
        overflow-y:    auto;
    }

    .node-content {
        background:    linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border:        2px solid #334155;
        border-radius: 12px;
        padding:       0;
        min-width:     300px;
        max-width:     450px;
        box-shadow:    0 8px 32px rgba(0, 0, 0, 0.8);
        overflow:      hidden;
    }

    .node-header {
        padding:       16px;
        background:    rgba(0, 0, 0, 0.3);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display:       flex;
        align-items:   center;
        gap:           12px;
    }

    .node-type-badge {
        background:     rgba(96, 165, 250, 0.2);
        color:          #60a5fa;
        padding:        4px 10px;
        border-radius:  6px;
        font-size:      10px;
        font-weight:    700;
        text-transform: uppercase;
        letter-spacing: 1px;
        border:         1px solid rgba(96, 165, 250, 0.3);
    }

    .node-title {
        font-size:   18px;
        font-weight: 700;
        color:       #f1f5f9;
        flex:        1;
    }

    .return-type-badge {
        background:    rgba(168, 85, 247, 0.15);
        color:         #a855f7;
        padding:       8px 12px;
        border-radius: 6px;
        font-size:     12px;
        margin:        12px 16px;
        display:       inline-block;
        font-family:   'Courier New', monospace;
        border:        1px solid rgba(168, 85, 247, 0.3);
    }

    .return-type-badge .label {
        opacity:        0.7;
        font-size:      10px;
        margin-right:   6px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .section-wrapper {
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .section-wrapper:last-of-type {
        border-bottom: none;
    }

    .section-header {
        padding:        12px 16px;
        background:     rgba(0, 0, 0, 0.2);
        font-size:      11px;
        font-weight:    700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color:          #94a3b8;
    }

    .params-list, .fields-preview, .methods-preview, .variants-list, .dependents-list {
        padding: 12px 16px;
    }

    .param-item, .field-item, .method-item, .variant-item, .dependent-item {
        padding:       8px 12px;
        margin-bottom: 6px;
        background:    rgba(255, 255, 255, 0.03);
        border-radius: 6px;
        font-family:   'Courier New', monospace;
        font-size:     12px;
        line-height:   1.6;
        transition:    all 0.2s ease;
        border-left:   3px solid transparent;
    }

    .param-item:hover, .field-item:hover, .method-item:hover, .variant-item:hover, .dependent-item:hover {
        background:  rgba(255, 255, 255, 0.06);
        border-left: 3px solid #60a5fa;
    }

    .param-item:last-child, .field-item:last-child, .method-item:last-child, 
    .variant-item:last-child, .dependent-item:last-child {
        margin-bottom: 0;
    }

    .param-name, .field-name, .method-name, .variant-name, .dependent-name {
        color:       #38bdf8;
        font-weight: 600;
    }

    .param-sep, .field-sep {
        color:  #64748b;
        margin: 0 6px;
    }

    .param-type, .field-type {
        color: #a78bfa;
    }

    .method-params {
        color:       #94a3b8;
        margin-left: 4px;
    }

    .method-return {
        color:       #10b981;
        margin-left: 8px;
    }

    .variant-fields {
        color:       #94a3b8;
        margin-left: 4px;
    }

    .visibility {
        background:     rgba(16, 185, 129, 0.2);
        color:          #10b981;
        padding:        2px 6px;
        border-radius:  4px;
        font-size:      10px;
        font-weight:    700;
        margin-right:   8px;
        text-transform: uppercase;
    }

    .visibility.private {
        background: rgba(248, 113, 113, 0.2);
        color:      #f87171;
    }

    .fn-pointer-badge {
        background:     rgba(245, 158, 11, 0.2);
        color:          #f59e0b;
        padding:        2px 6px;
        border-radius:  4px;
        font-size:      9px;
        font-weight:    700;
        margin-right:   8px;
        text-transform: uppercase;
        border:         1px solid rgba(245, 158, 11, 0.3);
    }

    .default-badge {
        background:     rgba(139, 92, 246, 0.2);
        color:          #8b5cf6;
        padding:        2px 6px;
        border-radius:  4px;
        font-size:      9px;
        font-weight:    700;
        margin-right:   8px;
        text-transform: uppercase;
        border:         1px solid rgba(139, 92, 246, 0.3);
    }

    .dep-type-badge {
        background:     rgba(236, 72, 153, 0.2);
        color:          #ec4899;
        padding:        2px 6px;
        border-radius:  4px;
        font-size:      9px;
        font-weight:    700;
        text-transform: uppercase;
        border:         1px solid rgba(236, 72, 153, 0.3);
        margin-right:   8px;
    }

    .dep-type-badge.struct   { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .dep-type-badge.function { background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
    .dep-type-badge.enum     { background: rgba(239, 68, 68, 0.2);  color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    .dep-type-badge.trait    { background: rgba(139, 92, 246, 0.2); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.3); }

    .file-info {
        padding:     12px 16px;
        background:  rgba(0, 0, 0, 0.3);
        font-size:   11px;
        color:       #64748b;
        font-style:  italic;
        display:     flex;
        align-items: center;
        gap:         8px;
    }

    .file-icon {
        font-size: 14px;
    }

    .dependent-item.more {
        opacity:    0.6;
        font-style: italic;
        color:      #94a3b8;
    }

    /* Scrollbar for tooltip */
    .node-tooltip::-webkit-scrollbar {
        width: 8px;
    }

    .node-tooltip::-webkit-scrollbar-track {
        background:    rgba(0, 0, 0, 0.3);
        border-radius: 4px;
    }

    .node-tooltip::-webkit-scrollbar-thumb {
        background:    rgba(96, 165, 250, 0.3);
        border-radius: 4px;
    }

    .node-tooltip::-webkit-scrollbar-thumb:hover {
        background: rgba(96, 165, 250, 0.5);
    }

    .legend {
        padding:       12px 20px;
        background:    rgba(0, 0, 0, 0.5);
        border-bottom: 1px solid rgba(96, 165, 250, 0.2);
        display:       flex;
        align-items:   center;
        gap:           20px;
    }

    .legend-title {
        font-size:   12px;
        font-weight: 700;
        color:       #94a3b8;
    }

    .legend-items {
        display:    flex;
        gap:        16px;
        flex-wrap:  wrap;
    }

    .legend-item {
        display:     flex;
        align-items: center;
        gap:         8px;
        font-size:   11px;
        color:       #cbd5e1;
    }

    .legend-line {
        width:  30px;
        height: 3px;
    }

    .edge-uses-line            { background: #60a5fa; }
    .edge-has-method-line      { background: #10b981; }
    .edge-fn-uses-type-line    { 
        background:    transparent;
        border-top:    2px dashed #fbbf24;
        border-bottom: none;
        height:        0;
    }
    .edge-fn-pointer-line      { 
        background:    transparent;
        border-top:    2px dotted #f59e0b;
        border-bottom: none;
        height:        0;
    }
    .edge-impl-trait-line      { background: #8b5cf6; }
    .edge-has-trait-impl-line  { 
        background:    transparent;
        border-top:    2px dashed #ec4899;
        border-bottom: none;
        height:        0;
    }
    '''
        
        with open(output_path / "styles.css", 'w') as f:
            f.write(css_content)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate interactive visualization of Rust code hierarchy'
    )
    parser.add_argument(
        'project_path',
        help='Path to the Rust project root directory'
    )
    parser.add_argument(
        '-o', '--output',
        default='output',
        help='Output directory for generated files (default: output)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"Error: Project path '{args.project_path}' does not exist")
        return 1
    
    print(f"Scanning Rust project at: {args.project_path}")
    print("=" * 60)
    
    parser_instance = RustParser(args.project_path)
    parser_instance.scan_project()
    
    print(f"\nFound {len(parser_instance.nodes)} items:")
    
    type_counts = {}
    for node in parser_instance.nodes.values():
        node_type = node.node_type.value
        type_counts[node_type] = type_counts.get(node_type, 0) + 1
    
    for node_type, count in sorted(type_counts.items()):
        print(f"  - {node_type:10s}: {count}")
    
    used_count   = sum(1 for n in parser_instance.nodes.values() if n.is_used)
    unused_count = len(parser_instance.nodes) - used_count
    
    print(f"\nUsage statistics:")
    print(f"  - Used items:   {used_count}")
    print(f"  - Unused items: {unused_count}")
    
    parser_instance.generate_output(args.output)
    
    return 0


if __name__ == "__main__":
    exit(main())
