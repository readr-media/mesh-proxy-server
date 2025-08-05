#!/usr/bin/env python3
"""
效能診斷工具
用於分析 /gql endpoint 的效能問題
"""

import json
import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any
import statistics

class PerformanceDiagnostic:
    def __init__(self, base_url: str, auth_token: str = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.results = []
        
    async def test_gql_endpoint(self, query: str, variables: Dict = None, num_requests: int = 10):
        """測試 GQL endpoint 的效能"""
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
            
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        print(f"開始測試 {num_requests} 次請求...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(num_requests):
                task = self._make_request(session, payload, headers, i)
                tasks.append(task)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        self.results = [r for r in results if not isinstance(r, Exception)]
        return self.analyze_results()
    
    async def _make_request(self, session: aiohttp.ClientSession, payload: Dict, headers: Dict, request_id: int):
        """執行單次請求並記錄時間"""
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.base_url}/gql",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                end_time = time.time()
                duration = end_time - start_time
                
                result = {
                    'request_id': request_id,
                    'duration': duration,
                    'status_code': response.status,
                    'response_size': len(await response.read()),
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"請求 {request_id}: {duration:.3f}s (狀態: {response.status})")
                return result
                
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                'request_id': request_id,
                'duration': duration,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"請求 {request_id}: {duration:.3f}s (錯誤: {e})")
            return result
    
    def analyze_results(self) -> Dict[str, Any]:
        """分析測試結果"""
        if not self.results:
            return {"error": "沒有有效的測試結果"}
            
        durations = [r['duration'] for r in self.results if 'duration' in r]
        status_codes = [r['status_code'] for r in self.results if 'status_code' in r]
        
        analysis = {
            'total_requests': len(self.results),
            'successful_requests': len([r for r in self.results if 'status_code' in r and r['status_code'] == 200]),
            'failed_requests': len([r for r in self.results if 'error' in r]),
            'duration_stats': {
                'min': min(durations) if durations else 0,
                'max': max(durations) if durations else 0,
                'mean': statistics.mean(durations) if durations else 0,
                'median': statistics.median(durations) if durations else 0,
                'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0,
                'p95': sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
                'p99': sorted(durations)[int(len(durations) * 0.99)] if durations else 0,
            },
            'status_code_distribution': {
                code: status_codes.count(code) for code in set(status_codes)
            },
            'slow_requests': [r for r in self.results if r.get('duration', 0) > 1.0],
            'fast_requests': [r for r in self.results if r.get('duration', 0) < 0.1],
        }
        
        return analysis
    
    def print_analysis(self, analysis: Dict[str, Any]):
        """印出分析結果"""
        print("\n" + "="*50)
        print("效能診斷結果")
        print("="*50)
        
        print(f"總請求數: {analysis['total_requests']}")
        print(f"成功請求: {analysis['successful_requests']}")
        print(f"失敗請求: {analysis['failed_requests']}")
        
        print("\n回應時間統計:")
        stats = analysis['duration_stats']
        print(f"  最小值: {stats['min']:.3f}s")
        print(f"  最大值: {stats['max']:.3f}s")
        print(f"  平均值: {stats['mean']:.3f}s")
        print(f"  中位數: {stats['median']:.3f}s")
        print(f"  標準差: {stats['std_dev']:.3f}s")
        print(f"  95%分位: {stats['p95']:.3f}s")
        print(f"  99%分位: {stats['p99']:.3f}s")
        
        print(f"\n慢請求 (>1s): {len(analysis['slow_requests'])}")
        print(f"快請求 (<0.1s): {len(analysis['fast_requests'])}")
        
        if analysis['slow_requests']:
            print("\n慢請求詳情:")
            for req in analysis['slow_requests'][:5]:  # 只顯示前5個
                print(f"  請求 {req['request_id']}: {req['duration']:.3f}s")
        
        print("\n狀態碼分佈:")
        for code, count in analysis['status_code_distribution'].items():
            print(f"  {code}: {count} 次")

async def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GQL Endpoint 效能診斷工具')
    parser.add_argument('--url', required=True, help='API 基礎 URL')
    parser.add_argument('--token', help='認證 token')
    parser.add_argument('--query', required=True, help='GraphQL 查詢')
    parser.add_argument('--variables', help='GraphQL 變數 (JSON 格式)')
    parser.add_argument('--requests', type=int, default=10, help='測試請求數量')
    
    args = parser.parse_args()
    
    # 解析變數
    variables = None
    if args.variables:
        try:
            variables = json.loads(args.variables)
        except json.JSONDecodeError:
            print("錯誤: 變數格式不是有效的 JSON")
            return
    
    # 建立診斷器
    diagnostic = PerformanceDiagnostic(args.url, args.token)
    
    # 執行測試
    analysis = await diagnostic.test_gql_endpoint(args.query, variables, args.requests)
    
    # 顯示結果
    diagnostic.print_analysis(analysis)
    
    # 儲存詳細結果
    with open(f'performance_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
        json.dump({
            'test_config': {
                'url': args.url,
                'query': args.query,
                'variables': variables,
                'num_requests': args.requests
            },
            'results': diagnostic.results,
            'analysis': analysis
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n詳細結果已儲存到 performance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

if __name__ == "__main__":
    asyncio.run(main()) 