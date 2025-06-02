import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from anytree import Node, NodeMixin, RenderTree
from anytree.search import find, findall
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class TreeDiff:
    """Tree differential analysis results"""
    added_nodes: List[str]
    removed_nodes: List[str]
    modified_nodes: List[str]
    moved_nodes: List[Tuple[str, str, str]]  # (node_name, old_parent, new_parent)
    timestamp: str
    
    def to_dict(self):
        return asdict(self)


class TreeSnapshot:
    """DOM tree snapshot manager"""
    
    def __init__(self, url: str, tree: Node, timestamp: Optional[str] = None):
        self.url = url
        self.timestamp = timestamp or datetime.now().isoformat()
        self.tree_hash = self._calculate_tree_hash(tree)
        self.node_signatures = self._extract_node_signatures(tree)
        
    def _calculate_tree_hash(self, tree: Node) -> str:
        """Calculate SHA hash of tree structure"""
        tree_str = ""
        for pre, _, node in RenderTree(tree):
            tree_str += f"{pre}{node.name}\n"
        return hashlib.md5(tree_str.encode()).hexdigest()
    def _extract_node_signatures(self, tree: Node) -> Dict[str, Dict]:
        """Extract unique signatures for each node"""
        signatures = {}
        
        def extract_recursive(node: Node, path: str = ""):
            current_path = f"{path}/{node.name}" if path else node.name
            
            signatures[current_path] = {
                'name': node.name,
                'parent': node.parent.name if node.parent else None,
                'children_count': len(node.children),
                'depth': node.depth,
                'path': current_path
            }
            
            for child in node.children:
                extract_recursive(child, current_path)
        
        extract_recursive(tree)
        return signatures


class TreeComparator:
    """Tree comparison and change detection engine"""
    
    def __init__(self, snapshots_dir: str = "snapshots"):
        self.snapshots_dir = snapshots_dir
        import os
        if not os.path.exists(snapshots_dir):
            os.makedirs(snapshots_dir)
    def save_snapshot(self, url: str, tree: Node) -> TreeSnapshot:
        """Persist tree snapshot to disk"""
        snapshot = TreeSnapshot(url, tree)
        
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{url_hash}_{snapshot.timestamp.replace(':', '-')}.json"
        filepath = f"{self.snapshots_dir}/{filename}"
        
        snapshot_data = {
            'url': snapshot.url,
            'timestamp': snapshot.timestamp,
            'tree_hash': snapshot.tree_hash,
            'node_signatures': snapshot.node_signatures
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Snapshot saved: {filepath}")
        return snapshot
    
    def load_snapshots(self, url: str) -> List[Dict]:
        """Load snapshots for specific URL"""
        import os
        import glob
        
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        pattern = f"{self.snapshots_dir}/{url_hash}_*.json"
        
        snapshots = []
        for filepath in glob.glob(pattern):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    snapshot_data = json.load(f)
                    snapshots.append(snapshot_data)
            except Exception as e:
                logging.warning(f"스냅샷 로드 실패 {filepath}: {e}")
        
        # 타임스탬프로 정렬
        snapshots.sort(key=lambda x: x['timestamp'])
        return snapshots
    def compare_trees(self, old_snapshot: Dict, new_snapshot: Dict) -> TreeDiff:
        """Compare two tree snapshots and detect structural differences"""
        old_signatures = old_snapshot['node_signatures']
        new_signatures = new_snapshot['node_signatures']
        
        old_paths = set(old_signatures.keys())
        new_paths = set(new_signatures.keys())
        
        # 추가된 노드
        added_nodes = list(new_paths - old_paths)
        
        # 제거된 노드
        removed_nodes = list(old_paths - new_paths)
        
        # 수정된 노드 (경로는 같지만 속성이 다른 노드)
        modified_nodes = []
        common_paths = old_paths & new_paths
        
        for path in common_paths:
            old_sig = old_signatures[path]
            new_sig = new_signatures[path]
            
            # 부모나 자식 수가 변경된 경우
            if (old_sig['parent'] != new_sig['parent'] or 
                old_sig['children_count'] != new_sig['children_count']):
                modified_nodes.append(path)
        
        # 이동된 노드 감지 (이름은 같지만 부모가 변경된 노드)
        moved_nodes = []
        for path in common_paths:
            old_sig = old_signatures[path]
            new_sig = new_signatures[path]
            
            if (old_sig['name'] == new_sig['name'] and 
                old_sig['parent'] != new_sig['parent'] and
                old_sig['parent'] is not None and new_sig['parent'] is not None):
                moved_nodes.append((
                    old_sig['name'], 
                    old_sig['parent'], 
                    new_sig['parent']
                ))
        
        return TreeDiff(
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
            modified_nodes=modified_nodes,
            moved_nodes=moved_nodes,
            timestamp=datetime.now().isoformat()
        )
    def detect_changes(self, url: str, current_tree: Node) -> Optional[TreeDiff]:
        """Detect changes between current tree and previous snapshot"""
        snapshots = self.load_snapshots(url)
        
        if not snapshots:
            self.save_snapshot(url, current_tree)
            logging.info("Initial snapshot saved")
            return None
        
        latest_snapshot = snapshots[-1]
        current_snapshot = TreeSnapshot(url, current_tree)
        
        if latest_snapshot['tree_hash'] == current_snapshot.tree_hash:
            logging.info("No structural changes detected")
            return None
        
        current_snapshot_dict = {
            'url': current_snapshot.url,
            'timestamp': current_snapshot.timestamp,
            'tree_hash': current_snapshot.tree_hash,
            'node_signatures': current_snapshot.node_signatures
        }
        diff = self.compare_trees(latest_snapshot, current_snapshot_dict)
        
        self.save_snapshot(url, current_tree)
        
        return diff
    
    def generate_diff_report(self, diff: TreeDiff) -> str:
        """Generate structural change analysis report"""
        report = f"=== Tree Change Analysis ({diff.timestamp}) ===\n\n"
        if diff.added_nodes:
            report += f"📝 Added nodes ({len(diff.added_nodes)}):\n"
            for node in diff.added_nodes:
                report += f"  + {node}\n"
            report += "\n"
        
        if diff.removed_nodes:
            report += f"🗑️ Removed nodes ({len(diff.removed_nodes)}):\n"
            for node in diff.removed_nodes:
                report += f"  - {node}\n"
            report += "\n"
        
        if diff.modified_nodes:
            report += f"🔄 Modified nodes ({len(diff.modified_nodes)}):\n"
            for node in diff.modified_nodes:
                report += f"  ~ {node}\n"
            report += "\n"
        
        if diff.moved_nodes:
            report += f"📦 Moved nodes ({len(diff.moved_nodes)}):\n"
            for node_name, old_parent, new_parent in diff.moved_nodes:
                report += f"  ↗️ {node_name}: {old_parent} → {new_parent}\n"
            report += "\n"
        
        if not any([diff.added_nodes, diff.removed_nodes, diff.modified_nodes, diff.moved_nodes]):
            report += "No changes detected.\n"
        
        return report