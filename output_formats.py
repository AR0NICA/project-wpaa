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
            
            html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>웹 페이지 구조 분석 - 인터랙티브 트리</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .controls {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .controls button {{
            margin: 0 5px;
            padding: 8px 16px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        
        .controls button:hover {{
            background-color: #0056b3;
        }}
        
        #tree-container {{
            width: 100%;
            height: 800px;
            border: 1px solid #ddd;
            background-color: white;
            overflow: auto;
        }}
        
        .node circle {{
            cursor: pointer;
            stroke: #333;
            stroke-width: 2px;
        }}
        
        .node.root circle {{
            fill: #ff6b6b;
        }}
        
        .node.internal circle {{
            fill: #4ecdc4;
        }}
        
        .node.leaf circle {{
            fill: #45b7d1;
        }}
        
        .node text {{
            font: 12px sans-serif;
            pointer-events: none;
        }}
        
        .link {{
            fill: none;
            stroke: #666;
            stroke-width: 1.5px;
        }}
        
        .tooltip {{
            position: absolute;
            text-align: left;
            padding: 8px;
            font: 12px sans-serif;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 4px;
            pointer-events: none;
            opacity: 0;
        }}
        
        .search-box {{
            margin: 10px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 200px;
        }}
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
        // 데이터
        const treeData = {json.dumps(json_data, ensure_ascii=False, indent=2)};
        
        // SVG 설정
        const margin = {{top: 20, right: 120, bottom: 20, left: 120}};
        const width = 1200 - margin.right - margin.left;
        const height = 800 - margin.top - margin.bottom;
        
        // SVG 생성
        const svg = d3.select("#tree-container")
            .append("svg")
            .attr("width", width + margin.right + margin.left)
            .attr("height", height + margin.top + margin.bottom);
        
        // 줌 기능
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});
        
        svg.call(zoom);
        
        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);
        
        // 트리 레이아웃
        const tree = d3.tree().size([height, width]);
        
        // 툴팁
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip");
        
        let root, i = 0;
        
        // 초기화
        function initialize() {{
            root = d3.hierarchy(treeData);
            root.x0 = height / 2;
            root.y0 = 0;
            
            // 초기에는 루트만 확장
            root.children.forEach(collapse);
            update(root);
        }}
        
        // 노드 축소
        function collapse(d) {{
            if (d.children) {{
                d._children = d.children;
                d._children.forEach(collapse);
                d.children = null;
            }}
        }}
        
        // 트리 업데이트
        function update(source) {{
            const treeData = tree(root);
            const nodes = treeData.descendants();
            const links = treeData.descendants().slice(1);
            
            // 노드 간격 조정
            nodes.forEach(d => d.y = d.depth * 180);
            
            // 노드 업데이트
            const node = g.selectAll('g.node')
                .data(nodes, d => d.id || (d.id = ++i));
            
            const nodeEnter = node.enter().append('g')
                .attr('class', d => {{
                    if (d.depth === 0) return 'node root';
                    if (d.children || d._children) return 'node internal';
                    return 'node leaf';
                }})
                .attr("transform", d => `translate(${{source.y0}},${{source.x0}})`)
                .on('click', click)
                .on('mouseover', showTooltip)
                .on('mouseout', hideTooltip);
            
            nodeEnter.append('circle')
                .attr('r', 1e-6);
            
            nodeEnter.append('text')
                .attr("dy", ".35em")
                .attr("x", d => d.children || d._children ? -13 : 13)
                .attr("text-anchor", d => d.children || d._children ? "end" : "start")
                .text(d => d.data.name)
                .style("fill-opacity", 1e-6);
            
            const nodeUpdate = nodeEnter.merge(node);
            
            nodeUpdate.transition()
                .duration(750)
                .attr("transform", d => `translate(${{d.y}},${{d.x}})`);
            
            nodeUpdate.select('circle')
                .attr('r', 6)
                .style("fill", d => d._children ? "lightsteelblue" : "#fff");
            
            nodeUpdate.select('text')
                .style("fill-opacity", 1);
            
            const nodeExit = node.exit().transition()
                .duration(750)
                .attr("transform", d => `translate(${{source.y}},${{source.x}})`)
                .remove();
            
            nodeExit.select('circle')
                .attr('r', 1e-6);
            
            nodeExit.select('text')
                .style('fill-opacity', 1e-6);
            
            // 링크 업데이트
            const link = g.selectAll('path.link')
                .data(links, d => d.id);
            
            const linkEnter = link.enter().insert('path', "g")
                .attr("class", "link")
                .attr('d', d => {{
                    const o = {{x: source.x0, y: source.y0}};
                    return diagonal(o, o);
                }});
            
            const linkUpdate = linkEnter.merge(link);
            
            linkUpdate.transition()
                .duration(750)
                .attr('d', d => diagonal(d, d.parent));
            
            const linkExit = link.exit().transition()
                .duration(750)
                .attr('d', d => {{
                    const o = {{x: source.x, y: source.y}};
                    return diagonal(o, o);
                }})
                .remove();
            
            nodes.forEach(d => {{
                d.x0 = d.x;
                d.y0 = d.y;
            }});
        }}
        
        // 대각선 경로 생성
        function diagonal(s, d) {{
            const path = `M ${{s.y}} ${{s.x}}
                        C ${{(s.y + d.y) / 2}} ${{s.x}},
                          ${{(s.y + d.y) / 2}} ${{d.x}},
                          ${{d.y}} ${{d.x}}`;
            return path;
        }}
        
        // 클릭 이벤트
        function click(event, d) {{
            if (d.children) {{
                d._children = d.children;
                d.children = null;
            }} else {{
                d.children = d._children;
                d._children = null;
            }}
            update(d);
        }}
        
        // 툴팁 표시
        function showTooltip(event, d) {{
            const nodeInfo = `
                <strong>${{d.data.name}}</strong><br/>
                깊이: ${{d.depth}}<br/>
                자식 수: ${{(d.children || d._children || []).length}}<br/>
                타입: ${{d.depth === 0 ? 'Root' : (d.children || d._children) ? 'Internal' : 'Leaf'}}
            `;
            
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            tooltip.html(nodeInfo)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
        }}
        
        // 툴팁 숨기기
        function hideTooltip() {{
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        }}
        
        // 전역 함수들
        function expandAll() {{
            root.descendants().forEach(d => {{
                if (d._children) {{
                    d.children = d._children;
                    d._children = null;
                }}
            }});
            update(root);
        }}
        
        function collapseAll() {{
            root.descendants().forEach(d => {{
                if (d.children) {{
                    d._children = d.children;
                    d.children = null;
                }}
            }});
            update(root);
        }}
        
        function resetZoom() {{
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
            );
        }}
        
        function downloadSVG() {{
            const svgElement = document.querySelector('#tree-container svg');
            const serializer = new XMLSerializer();
            const svgString = serializer.serializeToString(svgElement);
            
            const blob = new Blob([svgString], {{type: 'image/svg+xml'}});
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = 'tree-structure.svg';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
        
        // 검색 기능
        document.getElementById('searchBox').addEventListener('input', function(e) {{
            const searchTerm = e.target.value.toLowerCase();
            
            g.selectAll('g.node')
                .style('opacity', d => {{
                    if (!searchTerm) return 1;
                    return d.data.name.toLowerCase().includes(searchTerm) ? 1 : 0.3;
                }});
        }});
        
        // 초기화 실행
        initialize();
    </script>
</body>
</html>
            """
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logging.info(f"인터랙티브 HTML 파일이 {filename}에 저장되었습니다.")
            return filename
            
        except Exception as e:
            logging.error(f"HTML 출력 중 오류 발생: {e}")
            return None
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