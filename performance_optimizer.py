import asyncio
import aiohttp
import logging
import time
import psutil
import gc
import weakref
from functools import lru_cache, wraps
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import json
import pickle
import hashlib
from pathlib import Path

@dataclass
class PerformanceMetrics:
    """Performance metrics data container"""
    memory_usage_mb: float
    cpu_usage_percent: float
    execution_time_seconds: float
    cache_hit_ratio: float
    nodes_processed: int
    urls_processed: int

class MemoryManager:
    """Memory usage optimization manager"""
    
    def __init__(self, max_memory_mb: int = 1024):        
        self.max_memory_mb = max_memory_mb
        self.object_pool = weakref.WeakSet()
        self.large_objects = {}
    
    def monitor_memory(self):
        """Monitor current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        if memory_mb > self.max_memory_mb:
            logging.warning(f"Memory usage exceeded threshold: {memory_mb:.1f}MB")
            self.cleanup_memory()
        
        return memory_mb
    def cleanup_memory(self):
        """Memory cleanup operation"""
        # Force garbage collection        
        collected = gc.collect()
        logging.info(f"Garbage collection cleared {collected} objects")
        
        # Clear large objects
        self.clear_large_objects()
    
    def register_large_object(self, key: str, obj: Any):
        """대용량 객체 등록"""
        self.large_objects[key] = obj
    
    def clear_large_objects(self):
        """대용량 객체 정리"""
        cleared_count = len(self.large_objects)
        self.large_objects.clear()
        logging.info(f"{cleared_count}개 대용량 객체 정리")


class CacheManager:
    """향상된 캐싱 시스템"""
    
    def __init__(self, cache_dir: str = "cache", max_cache_size_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size_mb = max_cache_size_mb
        self.memory_cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        
        # 캐시 인덱스 파일
        self.index_file = self.cache_dir / "cache_index.json"
        self.load_cache_index()
    
    def load_cache_index(self):
        """캐시 인덱스 로드"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.cache_index = json.load(f)
            else:
                self.cache_index = {}
        except Exception as e:
            logging.warning(f"캐시 인덱스 로드 실패: {e}")
            self.cache_index = {}
    
    def save_cache_index(self):
        """캐시 인덱스 저장"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            logging.warning(f"캐시 인덱스 저장 실패: {e}")
    
    def get_cache_key(self, url: str, options: Dict = None) -> str:
        """캐시 키 생성"""
        key_data = f"{url}_{json.dumps(options or {}, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        # 메모리 캐시 우선 확인
        if cache_key in self.memory_cache:
            self.cache_stats['hits'] += 1
            return self.memory_cache[cache_key]
        
        # 디스크 캐시 확인
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    # 메모리 캐시에도 저장
                    self.memory_cache[cache_key] = data
                    self.cache_stats['hits'] += 1
                    return data
            except Exception as e:
                logging.warning(f"캐시 파일 로드 실패 {cache_file}: {e}")
        
        self.cache_stats['misses'] += 1
        return None
    
    def set(self, cache_key: str, data: Any):
        """캐시에 데이터 저장"""
        # 메모리 캐시에 저장
        self.memory_cache[cache_key] = data
        
        # 디스크 캐시에 저장
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            # 캐시 인덱스 업데이트
            self.cache_index[cache_key] = {
                'file': str(cache_file),
                'timestamp': time.time(),
                'size_bytes': cache_file.stat().st_size
            }
            
        except Exception as e:
            logging.warning(f"캐시 저장 실패 {cache_file}: {e}")
    
    def cleanup_old_cache(self, max_age_days: int = 7):
        """오래된 캐시 정리"""
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        removed_count = 0
        for cache_key, info in list(self.cache_index.items()):
            if current_time - info['timestamp'] > max_age_seconds:
                cache_file = Path(info['file'])
                if cache_file.exists():
                    cache_file.unlink()
                del self.cache_index[cache_key]
                removed_count += 1
        
        if removed_count > 0:
            logging.info(f"{removed_count}개 오래된 캐시 파일 정리")
            self.save_cache_index()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_ratio = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0
        
        total_size_bytes = sum(info['size_bytes'] for info in self.cache_index.values())
        
        return {
            'hit_ratio': hit_ratio,
            'total_requests': total_requests,
            'cache_files': len(self.cache_index),
            'total_size_mb': total_size_bytes / 1024 / 1024
        }


class PerformanceOptimizer:
    """성능 최적화를 관리하는 메인 클래스"""
    
    def __init__(self, max_workers: int = 4, max_memory_mb: int = 1024):
        self.max_workers = max_workers
        self.memory_manager = MemoryManager(max_memory_mb)
        self.cache_manager = CacheManager()
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.performance_history = []
    
    def performance_monitor(self, func):
        """성능 모니터링 데코레이터"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = self.memory_manager.monitor_memory()
            start_cpu = psutil.cpu_percent()
            
            try:
                result = await func(*args, **kwargs)
                
                # 성능 메트릭 수집
                end_time = time.time()
                end_memory = self.memory_manager.monitor_memory()
                end_cpu = psutil.cpu_percent()
                
                cache_stats = self.cache_manager.get_cache_stats()
                
                metrics = PerformanceMetrics(
                    memory_usage_mb=end_memory,
                    cpu_usage_percent=end_cpu,
                    execution_time_seconds=end_time - start_time,
                    cache_hit_ratio=cache_stats['hit_ratio'],
                    nodes_processed=getattr(result, 'node_count', 0) if result else 0,
                    urls_processed=1
                )
                
                self.performance_history.append(metrics)
                
                # 성능 로그
                logging.info(f"성능 메트릭 - 실행시간: {metrics.execution_time_seconds:.2f}s, "
                           f"메모리: {metrics.memory_usage_mb:.1f}MB, "
                           f"캐시 적중률: {metrics.cache_hit_ratio:.2%}")
                
                return result
                
            except Exception as e:
                logging.error(f"성능 모니터링 중 오류 발생: {e}")
                raise
        
        return wrapper
    
    @lru_cache(maxsize=1000)
    def get_optimized_options(self, url: str, max_depth: int = None) -> Dict[str, Any]:
        """URL별 최적화된 옵션 반환"""
        # URL 패턴에 따른 최적화 옵션
        options = {
            'exclude': ['script', 'style', 'meta', 'link'],
            'max_depth': max_depth or 10,
            'include_text': False
        }
        
        # 도메인별 특별 옵션
        if 'github.com' in url:
            options['exclude'].extend(['svg', 'path'])
            options['max_depth'] = 8
        elif 'stackoverflow.com' in url:
            options['custom_filter'] = '.question, .answer'
        elif 'wikipedia.org' in url:
            options['custom_filter'] = '#content'
            options['max_depth'] = 6
        
        return options
    
    async def batch_process_urls(self, urls: List[str], analysis_func, options: Dict = None) -> List[Any]:
        """URL 배치 처리"""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_single_url(url: str):
            async with semaphore:
                cache_key = self.cache_manager.get_cache_key(url, options)
                
                # 캐시 확인
                cached_result = self.cache_manager.get(cache_key)
                if cached_result:
                    logging.info(f"캐시에서 로드: {url}")
                    return cached_result
                
                # 분석 실행
                try:
                    result = await analysis_func(url, options or {})
                    if result:
                        self.cache_manager.set(cache_key, result)
                    return result
                except Exception as e:
                    logging.error(f"URL 처리 실패 {url}: {e}")
                    return None
        
        # 병렬 처리
        tasks = [process_single_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logging.error(f"URL {urls[i]} 처리 중 예외 발생: {result}")
            elif result is not None:
                valid_results.append(result)
        
        return valid_results
    
    def optimize_tree_structure(self, tree_data: Dict, max_children: int = 50) -> Dict:
        """트리 구조 최적화"""
        def optimize_node(node: Dict) -> Dict:
            if 'children' in node and len(node['children']) > max_children:
                # 자식 노드가 너무 많으면 그룹화
                children = node['children']
                grouped_children = []
                
                # 태그 타입별로 그룹화
                tag_groups = {}
                for child in children:
                    tag_name = child.get('name', '').split()[0]  # 첫 번째 단어만 사용
                    if tag_name not in tag_groups:
                        tag_groups[tag_name] = []
                    tag_groups[tag_name].append(child)
                
                # 그룹이 너무 클 경우 대표 노드만 유지
                for tag_name, group in tag_groups.items():
                    if len(group) > 10:
                        summary_node = {
                            'name': f"{tag_name} ({len(group)}개)",
                            'children': group[:5]  # 처음 5개만 유지
                        }
                        grouped_children.append(summary_node)
                    else:
                        grouped_children.extend(group)
                
                node['children'] = grouped_children
            
            # 재귀적으로 자식 노드들도 최적화
            if 'children' in node:
                for child in node['children']:
                    optimize_node(child)
            
            return node
        
        return optimize_node(tree_data.copy())
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 보고서 생성"""
        if not self.performance_history:
            return {'message': '성능 데이터가 없습니다.'}
        
        recent_metrics = self.performance_history[-10:]  # 최근 10개
        
        avg_execution_time = sum(m.execution_time_seconds for m in recent_metrics) / len(recent_metrics)
        avg_memory_usage = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
        avg_cache_hit_ratio = sum(m.cache_hit_ratio for m in recent_metrics) / len(recent_metrics)
        
        cache_stats = self.cache_manager.get_cache_stats()
        
        return {
            'average_execution_time': avg_execution_time,
            'average_memory_usage_mb': avg_memory_usage,
            'average_cache_hit_ratio': avg_cache_hit_ratio,
            'total_analyses': len(self.performance_history),
            'cache_statistics': cache_stats,
            'optimization_recommendations': self._get_optimization_recommendations()
        }
    
    def _get_optimization_recommendations(self) -> List[str]:
        """최적화 권장사항 생성"""
        recommendations = []
        
        if not self.performance_history:
            return recommendations
        
        recent_metrics = self.performance_history[-5:]
        
        # 실행 시간 분석
        avg_time = sum(m.execution_time_seconds for m in recent_metrics) / len(recent_metrics)
        if avg_time > 30:
            recommendations.append("실행 시간이 긴 편입니다. max_depth 설정을 낮춰보세요.")
        
        # 메모리 사용량 분석
        avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
        if avg_memory > 500:
            recommendations.append("메모리 사용량이 높습니다. 제외할 태그를 더 추가하거나 텍스트 포함을 비활성화하세요.")
        
        # 캐시 적중률 분석
        cache_stats = self.cache_manager.get_cache_stats()
        if cache_stats['hit_ratio'] < 0.3:
            recommendations.append("캐시 적중률이 낮습니다. 동일한 URL을 재분석하는 것을 고려해보세요.")
        
        if not recommendations:
            recommendations.append("현재 성능이 양호합니다.")
        
        return recommendations
    
    def cleanup(self):
        """리소스 정리"""
        self.thread_pool.shutdown(wait=True)
        self.memory_manager.cleanup_memory()
        self.cache_manager.cleanup_old_cache()
        self.cache_manager.save_cache_index()


# 전역 성능 최적화 인스턴스
_optimizer_instance = None

def get_optimizer() -> PerformanceOptimizer:
    """전역 성능 최적화 인스턴스 반환"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = PerformanceOptimizer()
    return _optimizer_instance