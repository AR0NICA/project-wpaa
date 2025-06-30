import json
import logging
from typing import Optional, Dict, Any
from anytree import Node, RenderTree
from anytree.exporter import JsonExporter
import xml.etree.ElementTree as ET


class OutputFormatter:
    """Multi-format tree export engine"""
    
    def __init__(self):
        self.svg_styles = """
        <style>
            .node-rect { fill: #e1f5fe; stroke: #01579b; stroke-width: 1; }
            .node-text { font-family: Arial, sans-serif; font-size: 12px; fill: #000; }
            .edge-line { stroke: #666; stroke-width: 1; }
            .root-node { fill: #ffecb3; stroke: #ff8f00; }
            .leaf-node { fill: #f3e5f5; stroke: #4a148c; }
        </style>
        """
    
    def export_to_svg(self, root: Node, filename: str = "tree_structure.svg", 
                     width: int = 1200, height: int = 800) -> str:
        """Export tree as SVG with vector graphics"""
        try:
            svg = ET.Element("svg", {
                "xmlns": "http://www.w3.org/2000/svg",
                "width": str(width),
                "height": str(height),
                "viewBox": f"0 0 {width} {height}"
            })
            
            style_element = ET.SubElement(svg, "style")
            style_element.text = self.svg_styles
            
            node_positions = self._calculate_node_positions(root, width, height)
            
            self._draw_edges(svg, root, node_positions)
            
            self._draw_nodes(svg, root, node_positions)
            
            # SVG 파일 저장
            tree = ET.ElementTree(svg)
            tree.write(filename, encoding='utf-8', xml_declaration=True)
            
            logging.info(f"SVG 파일이 {filename}에 저장되었습니다.")
            return filename
            
        except Exception as e:            
            logging.error(f"SVG export error: {e}")
            return None
    
    def _calculate_node_positions(self, root: Node, width: int, height: int) -> Dict[Node, tuple]:
        """Calculate optimal node positioning"""
        positions = {}
        
        max_depth = max(node.depth for node in root.descendants) + 1
        
        level_counts = {}
        for node in [root] + list(root.descendants):
            level = node.depth
            level_counts[level] = level_counts.get(level, 0) + 1
        
        level_indices = {level: 0 for level in level_counts}
        
        for node in [root] + list(root.descendants):
            level = node.depth
            level_index = level_indices[level]
            
            if level_counts[level] == 1:
                x = width // 2
            else:
                x = (width * (level_index + 1)) // (level_counts[level] + 1)
            
            y = (height * (level + 1)) // (max_depth + 1)
            
            positions[node] = (x, y)
            level_indices[level] += 1
        
        return positions
    
    def _draw_edges(self, svg: ET.Element, root: Node, positions: Dict[Node, tuple]):
        """Render connection lines between nodes"""
        for node in [root] + list(root.descendants):
            if node.parent:
                parent_x, parent_y = positions[node.parent]
                child_x, child_y = positions[node]
                
                line = ET.SubElement(svg, "line", {
                    "x1": str(parent_x),
                    "y1": str(parent_y + 15),
                    "x2": str(child_x),
                    "y2": str(child_y - 15),
                    "class": "edge-line"
                })
    
    def _draw_nodes(self, svg: ET.Element, root: Node, positions: Dict[Node, tuple]):
        """Render DOM tree nodes with styling"""
        for node in [root] + list(root.descendants):
            x, y = positions[node]
            
            # 노드 타입에 따른 스타일 결정
            if node == root:
                node_class = "node-rect root-node"
            elif not node.children:
                node_class = "node-rect leaf-node"
            else:
                node_class = "node-rect"
            
            # 텍스트 길이에 따른 박스 크기 조정
            text_width = max(len(node.name) * 8, 80)
            
            # 노드 박스
            rect = ET.SubElement(svg, "rect", {
                "x": str(x - text_width // 2),
                "y": str(y - 15),
                "width": str(text_width),
                "height": "30",
                "class": node_class,
                "rx": "5"
            })
            
            # 노드 텍스트
            text = ET.SubElement(svg, "text", {
                "x": str(x),
                "y": str(y + 5),
                "text-anchor": "middle",
                "class": "node-text"
            })
            text.text = node.name[:20] + "..." if len(node.name) > 20 else node.name

    def export_to_interactive_html(self, root: Node, filename: str = "tree_interactive.html") -> str:
        """Export as interactive HTML with D3.js visualization"""
        try:
            # JSON 데이터 생성
            json_data = self._tree_to_d3_format(root)
            
            # HTML 템플릿 파일 읽기
            html_content = self._load_html_template(json_data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logging.info(f"인터랙티브 HTML 파일이 {filename}에 저장되었습니다.")
            return filename
            
        except Exception as e:
            logging.error(f"HTML 출력 중 오류 발생: {e}")
            return None
    def _load_html_template(self, json_data: Dict[str, Any]) -> str:
        """HTML 템플릿 파일을 로드하고 데이터를 삽입"""
        import os
        
        # 템플릿 파일 경로 설정
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'interactive_tree.html')
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # JSON 데이터를 템플릿에 삽입
            html_content = template_content.replace(
                '{{TREE_DATA}}', 
                json.dumps(json_data, ensure_ascii=False, indent=2)
            )
            
            return html_content
            
        except FileNotFoundError:
            logging.warning(f"템플릿 파일을 찾을 수 없습니다: {template_path}")
            return self._get_fallback_html_template(json_data)
    def _get_fallback_html_template(self, json_data: Dict[str, Any]) -> str:
        """템플릿 파일이 없을 때 사용할 기본 HTML 템플릿"""
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>웹 페이지 구조 분석 - 인터랙티브 트리</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .header {{ text-align: center; margin-bottom: 20px; }}
        .controls {{ text-align: center; margin-bottom: 20px; }}
        .controls button {{ margin: 0 5px; padding: 8px 16px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
        #tree-container {{ width: 100%; height: 800px; border: 1px solid #ddd; background-color: white; overflow: auto; }}
        .node circle {{ cursor: pointer; stroke: #333; stroke-width: 2px; }}
        .node.root circle {{ fill: #ff6b6b; }}
        .node.internal circle {{ fill: #4ecdc4; }}
        .node.leaf circle {{ fill: #45b7d1; }}
        .node text {{ font: 12px sans-serif; pointer-events: none; }}
        .link {{ fill: none; stroke: #666; stroke-width: 1.5px; }}
        .tooltip {{ position: absolute; text-align: left; padding: 8px; font: 12px sans-serif; background: rgba(0, 0, 0, 0.8); color: white; border-radius: 4px; pointer-events: none; opacity: 0; }}
        .search-box {{ margin: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 200px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>웹 페이지 HTML 구조 분석</h1>
        <p>노드를 클릭하여 확장/축소하고, 마우스를 올려 세부 정보를 확인하세요.</p>
    </div>
    <div class="controls">
        <input type="text" class="search-box" placeholder="노드 검색..." id="searchBox">
        <button onclick="expandAll()">모두 확장</button>
        <button onclick="collapseAll()">모두 축소</button>
        <button onclick="resetZoom()">줌 리셋</button>
        <button onclick="downloadSVG()">SVG 다운로드</button>
    </div>
    <div id="tree-container"></div>
    <script>
        const treeData = {json.dumps(json_data, ensure_ascii=False, indent=2)};
        // 간단한 D3.js 스크립트 (기본 기능만 포함)
        console.log("Tree data loaded:", treeData);
    </script>
</body>
</html>"""

    def _tree_to_d3_format(self, node: Node) -> Dict[str, Any]:
        """Convert anytree Node to D3.js hierarchical data format"""
        result = {
            "name": node.name,
            "children": []
        }
        
        for child in node.children:
            result["children"].append(self._tree_to_d3_format(child))
        
        if not result["children"]:
            del result["children"]
        
        return result
    def export_to_csv(self, root: Node, filename: str = "tree_structure.csv") -> str:
        """Export tree structure as CSV data format"""
        try:
            import csv
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Path', 'Node Name', 'Depth', 'Parent', 'Children Count'])
                
                for pre, _, node in RenderTree(root):
                    path = "/".join([n.name for n in node.path])
                    parent_name = node.parent.name if node.parent else ""
                    children_count = len(node.children)
                    
                    writer.writerow([
                        path,
                        node.name,
                        node.depth,
                        parent_name,
                        children_count
                    ])
            
            logging.info(f"CSV 파일이 {filename}에 저장되었습니다.")
            return filename
            
        except Exception as e:
            logging.error(f"CSV 출력 중 오류 발생: {e}")
            return None
    def export_to_markdown(self, root: Node, filename: str = "tree_structure.md") -> str:
        """Export tree structure as Markdown documentation"""
        try:
            content = "# 웹 페이지 HTML 구조 분석\n\n"
            content += f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += "## 트리 구조\n\n```\n"
            
            for pre, _, node in RenderTree(root):
                content += f"{pre}{node.name}\n"
            
            content += "```\n\n"
            
            # 통계 정보 추가
            all_nodes = [root] + list(root.descendants)
            content += "## 통계\n\n"
            content += f"- 총 노드 수: {len(all_nodes)}\n"
            content += f"- 최대 깊이: {max(node.depth for node in all_nodes)}\n"
            content += f"- 리프 노드 수: {len([n for n in all_nodes if not n.children])}\n"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logging.info(f"마크다운 파일이 {filename}에 저장되었습니다.")
            return filename
            
        except Exception as e:
            logging.error(f"마크다운 출력 중 오류 발생: {e}")
            return None


# 추가 의존성을 위한 datetime import
from datetime import datetime