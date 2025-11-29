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
    FUNCTION = "function"
    STRUCT   = "struct"
    ENUM     = "enum"
    TRAIT    = "trait"
    IMPL     = "impl"
    MODULE   = "module"

@dataclass
class Field:
    name:           str
    type_name:      str
    is_public:      bool = True
    is_fn_pointer:  bool = False
    fn_pointer_sig: str  = ""

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
        types           = []
        generic_pattern = r'<([^<>]+(?:<[^<>]+>)*)>'
        matches         = re.findall(generic_pattern, type_name)
        
        for match in matches:
            depth   = 0
            current = ""
            for char in match:
                if char == '<':
                    depth += 1
                elif char == '>':
                    depth -= 1
                elif char == ',' and depth == 0:
                    if current.strip():
                        types.append(current.strip())
                    current = ""
                    continue
                current += char
            
            if current.strip():
                types.append(current.strip())
        
        return types

    def scan_project(self):
        """Scan all Rust files in the project, excluding target directory"""
        rust_files = []
        
        for rust_file in self.project_root.rglob("*.rs"):
            # Skip target directory
            if 'target' in rust_file.parts:
                continue
            rust_files.append(rust_file)
        
        print(f"Found {len(rust_files)} Rust files (excluding target/)")
        
        for rust_file in rust_files:
            self._parse_file(rust_file)
        
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
        methods        = []
        method_pattern = r'(?:pub\s+)?fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^{;]+))?'
        
        for match in re.finditer(method_pattern, impl_body):
            method_name = match.group(1)
            params_str  = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else ""
            is_public   = 'pub' in impl_body[max(0, match.start()-10):match.start()]
            
            params = self._parse_params(params_str)
            
            methods.append(Method(
                name        = method_name,
                params      = params,
                return_type = return_type,
                is_public   = is_public
            ))
        
        return methods

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
        fn_pattern = r'(?:pub\s+)?fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^{;]+))?'
        
        for match in re.finditer(fn_pattern, content):
            fn_name     = match.group(1)
            params_str  = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else ""
            is_public   = 'pub' in content[max(0, match.start()-10):match.start()]
            
            # Skip if this is inside an impl block
            before_text = content[:match.start()]
            if 'impl' in before_text.split('\n')[-5:]:
                impl_depth = before_text.count('{') - before_text.count('}')
                if impl_depth > 0:
                    continue
            
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

    def _mark_usage(self):
        """Mark which nodes are used by others"""
        for node in self.nodes.values():
            for linked_type in node.linked_types:
                target_node = self._find_node_by_type(linked_type)
                if target_node:
                    target_node.is_used = True

    def _build_tree_structure(self) -> List[Dict]:
        """Build tree structure with parent-child relationships using resolved paths"""
        # Build parent-child relationships using resolved type paths
        for node in self.nodes.values():
            for linked_type in node.linked_types:
                target_node = self._find_node_by_type(linked_type)
                if target_node and target_node not in node.children:
                    node.children.append(target_node)
        
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
        
        # Build tree data
        tree_data = self._build_treant_data()
        
        # Generate HTML with embedded data
        self._generate_html(output_path, tree_data)
        
        # Generate CSS
        self._generate_css(output_path)
        
        print(f"\nVisualization generated in '{output_dir}/' directory")
        print(f"Open '{output_dir}/index.html' in your browser")

    def _build_treant_data(self) -> Dict:
        """Build data structure for Treant.js"""
        root_nodes      = self._build_tree_structure()
        processed_nodes = set()
        
        def node_to_treant(node: Node, depth: int = 0) -> Dict:
            if node.id in processed_nodes or depth > 5:
                return None
            
            processed_nodes.add(node.id)
            
            # Build HTML content for node with expandable sections
            html_parts = [
                '<div class="node-content">',
                f'<div class="node-header">',
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
            
            # Parameters section
            if node.params:
                all_params     = node.params
                
                html_parts.append('<div class="section-wrapper">')
                html_parts.append('<div class="section-header">Parameters</div>')
                html_parts.append('<div class="params-list">')


                for param in all_params:
                    html_parts.append(
                        f'<div class="param-item">'
                        f'<span class="param-name">{param.name}</span>'
                        f'<span class="param-sep">:</span>'
                        f'<span class="param-type">{param.type_name}</span>'
                        f'</div>'
                    )
                html_parts.append('</div>')  # Close full

                html_parts.append('</div>')  # Close section-wrapper
            
            # Fields section
            if node.fields:
                all_fields     = node.fields
                
                html_parts.append('<div class="section-wrapper">')
                html_parts.append('<div class="section-header">Fields</div>')
                html_parts.append('<div class="fields-preview">')


                for field in all_fields:
                    vis = '<span class="visibility">pub</span> ' if field.is_public else '<span class="visibility private">priv</span> '
                    fn_badge = '<span class="fn-pointer-badge">fn ptr</span> ' if field.is_fn_pointer else ''
                    html_parts.append(
                        f'<div class="field-item">'
                        f'{vis}'
                        f'{fn_badge}'
                        f'<span class="field-name">{field.name}</span>'
                        f'<span class="field-sep">:</span>'
                        f'<span class="field-type">{field.type_name}</span>'
                        f'</div>'
                    )
                html_parts.append('</div>')
                html_parts.append('</div>')

            # Methods section
            if node.methods:
                all_methods     = node.methods
                
                html_parts.append('<div class="section-wrapper">')
                html_parts.append('<div class="section-header">Methods</div>')
                html_parts.append('<div class="methods-preview">')

                html_parts.append('<div class="methods-full" style="display:none;">')
                
                for method in all_methods:
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
                html_parts.append('</div>')  # Close full
                html_parts.append('</div>')  # Close section-wrapper

            if node.variants:
                html_parts.append('<div class="section-wrapper">')
                html_parts.append('<div class="section-header">Variants</div>')
                html_parts.append('<div class="variants-list">')  # Changed from variants-preview
                
                for variant in node.variants:  # Changed from preview_variants to node.variants
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

                html_parts.append('</div>')  # Close variants-list
                html_parts.append('</div>')  # Close section-wrapper

            html_parts.append(f'<div class="file-info"><span class="file-icon">📁</span> {node.file_path}</div>')
            html_parts.append('</div>')  # Close node-content
            
            result = {
                'text': {
                    'name': node.name
                },
                'HTMLclass': f'{node.node_type.value} {"unused" if not node.is_used else ""}',
                'innerHTML': ''.join(html_parts)
            }
            
            children = []
            for child in node.children:
                child_data = node_to_treant(child, depth + 1)
                if child_data:
                    children.append(child_data)
            
            if children:
                result['children'] = children
            
            return result
        
        chart_structure = []
        for root in root_nodes[:20]:  # Limit to 20 root nodes
            root_data = node_to_treant(root)
            if root_data:
                chart_structure.append(root_data)
        
        return {
            'chart': {
                'container': '#tree-container',
                'levelSeparation': 40,
                'siblingSeparation': 20,
                'subTeeSeparation': 40,
                'rootOrientation': 'NORTH',
                'nodeAlign': 'CENTER',
                'connectors': {
                    'type': 'step'
                },
                'node': {
                    'collapsable': True
                }
            },
            'nodeStructure': chart_structure
        }

    def _generate_html(self, output_path: Path, tree_data: Dict):
        """Generate HTML file with Treant.js visualization"""
        tree_json = json.dumps(tree_data, indent=2)
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rust Code Hierarchy</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/treant-js/1.0/Treant.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/raphael/2.3.0/raphael.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/treant-js/1.0/Treant.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>Rust Code Hierarchy Visualization</h1>
        <div id="tree-container"></div>
    </div>
    
    <script>
        const tree_data = {tree_json};
        
        // Initialize trees
        const trees    = [];
        let all_nodes  = [];
        
        tree_data.nodeStructure.forEach((root, index) => {{
            const container = document.createElement('div');
            container.className = 'tree-wrapper';
            container.id = 'tree-' + index;
            document.getElementById('tree-container').appendChild(container);
            
            const config = {{
                ...tree_data.chart,
                container: '#tree-' + index
            }};
            
            const tree = new Treant({{
                chart: config,
                nodeStructure: root
            }});
            
            trees.push(tree);
        }});
        
        // Wait for DOM to be ready, then collect all nodes
        setTimeout(() => {{
            all_nodes = document.querySelectorAll('.Treant .node');
        }}, 500);
        
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
    padding:     20px;
    min-height:  100vh;
}

.container {
    max-width: 100%;
}

h1 {
    color:          #60a5fa;
    margin-bottom:  20px;
    font-size:      2rem;
    font-weight:    700;
    text-shadow:    0 0 20px rgba(96, 165, 250, 0.3);
    letter-spacing: -0.5px;
}

.controls {
    margin-bottom: 20px;
    display:       flex;
    gap:           12px;
}

.controls button {
    background:    linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color:         white;
    border:        none;
    padding:       12px 24px;
    cursor:        pointer;
    border-radius: 8px;
    font-size:     14px;
    font-weight:   600;
    transition:    all 0.3s ease;
    box-shadow:    0 4px 6px rgba(0, 0, 0, 0.3);
}

.controls button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    transform:  translateY(-2px);
    box-shadow: 0 6px 12px rgba(59, 130, 246, 0.4);
}

#tree-container {
    border:        1px solid rgba(96, 165, 250, 0.2);
    border-radius: 12px;
    padding:       40px;
    overflow:      scroll;
}

.tree-wrapper {
    margin-bottom: 60px;
}

.Treant {
    width:  100%;
    height: auto;
}

.Treant .node {
    background:    linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
    border:        2px solid #334155;
    border-radius: 12px;
    padding:       0;
    min-width:     250px;
    max-width:     350px;
    cursor:        pointer;
    transition:    all 0.3s ease;
    box-shadow:    0 4px 12px rgba(0, 0, 0, 0.5);
    overflow:      hidden;
}

.Treant .node:hover {
    transform:  translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
    opacity: 0.8
}

.Treant .node.struct {
    border-color: #10b981;
    background:   linear-gradient(145deg, #064e3b 0%, #022c22 100%);
}

.Treant .node.function {
    border-color: #f59e0b;
    background:   linear-gradient(145deg, #78350f 0%, #451a03 100%);
}

.Treant .node.enum {
    border-color: #ef4444;
    background:   linear-gradient(145deg, #7f1d1d 0%, #450a0a 100%);
}

.Treant .node.unused {
    filter:  grayscale(1);
}

.node-content {
    padding: 0;
}

.node-header {
    padding:          16px;
    background:       rgba(0, 0, 0, 0.3);
    border-bottom:    1px solid rgba(255, 255, 255, 0.1);
    display:          flex;
    align-items:      center;
    gap:              12px;
}

.node-type-badge {
    background:    rgba(96, 165, 250, 0.2);
    color:         #60a5fa;
    padding:       4px 10px;
    border-radius: 6px;
    font-size:     10px;
    font-weight:   700;
    text-transform: uppercase;
    letter-spacing: 1px;
    border:        1px solid rgba(96, 165, 250, 0.3);
}

.node.struct .node-type-badge {
    background: rgba(16, 185, 129, 0.2);
    color:      #10b981;
    border:     1px solid rgba(16, 185, 129, 0.3);
}

.node.function .node-type-badge {
    background: rgba(245, 158, 11, 0.2);
    color:      #f59e0b;
    border:     1px solid rgba(245, 158, 11, 0.3);
}

.node.enum .node-type-badge {
    background: rgba(239, 68, 68, 0.2);
    color:      #ef4444;
    border:     1px solid rgba(239, 68, 68, 0.3);
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
    font-family:   'JetBrainsMono Nerd Font', monospace;
    border:        1px solid rgba(168, 85, 247, 0.3);
}

.return-type-badge .label {
    opacity:     0.7;
    font-size:   10px;
    margin-right: 6px;
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

.params-list, .fields-list, .methods-list, .variants-list {
    padding: 12px 16px;
}

.param-item, .field-item, .method-item, .variant-item {
    padding:       8px 12px;
    margin-bottom: 6px;
    background:    rgba(255, 255, 255, 0.03);
    border-radius: 6px;
    font-family:   'JetBrainsMono Nerd Font', monospace;
    font-size:     13px;
    line-height:   1.6;
    transition:    all 0.2s ease;
    border-left:   3px solid transparent;
}

.param-item:hover, .field-item:hover, .method-item:hover, .variant-item:hover {
    background:  rgba(255, 255, 255, 0.06);
    border-left: 3px solid #60a5fa;
    transform:   translateX(2px);
}

.param-item:last-child, .field-item:last-child, .method-item:last-child, .variant-item:last-child {
    margin-bottom: 0;
}

.param-name, .field-name, .method-name, .variant-name {
    color:       #38bdf8;
    font-weight: 600;
}

.param-sep, .field-sep {
    color:   #64748b;
    margin:  0 6px;
}

.param-type, .field-type {
    color: #a78bfa;
}

.method-params {
    color:   #94a3b8;
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
    background:    rgba(16, 185, 129, 0.2);
    color:         #10b981;
    padding:       2px 6px;
    border-radius: 4px;
    font-size:     10px;
    font-weight:   700;
    margin-right:  8px;
    text-transform: uppercase;
}

.visibility.private {
    background: rgba(100, 116, 139, 0.2);
    color:      #f78baa;
}

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

.Treant .collapse-switch {
    width:         24px;
    height:        24px;
    border:        2px solid #60a5fa;
    background:    #1e293b;
    border-radius: 50%;
    transition:    all 0.3s ease;
}

.Treant .collapse-switch:hover {
    background: #60a5fa;
    transform:  scale(1.1);
    box-shadow: 0 0 12px rgba(96, 165, 250, 0.5);
}

.Treant path {
    stroke:         #60a5fa;
    stroke-width:   6px;
    opacity:        0.6;
    filter:         drop-shadow(0 0 2px rgba(0, 0, 0, 0.8));
}
.Treant path:hover {
    stroke:  #ffffff;
    filter:  drop-shadow(0 0 2px 1px rgba(255, 255, 255, 0.8));
    opacity: 1;

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

/* Scrollbar styling */
#tree-container::-webkit-scrollbar {
    width:  12px;
    height: 12px;
}

#tree-container::-webkit-scrollbar-track {
    background:    rgba(0, 0, 0, 0.3);
    border-radius: 6px;
}

#tree-container::-webkit-scrollbar-thumb {
    background:    rgba(96, 165, 250, 0.3);
    border-radius: 6px;
    transition:    all 0.3s ease;
}

#tree-container::-webkit-scrollbar-thumb:hover {
    background: rgba(96, 165, 250, 0.5);
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
