#!/usr/bin/env python3
"""
并发 API 测试脚本
测试多 key 轮询是否正常工作
"""
import asyncio
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from app.ai.llm import generate_reply, call_llm_json, _api_keys

def test_simple_chat(index: int):
    """测试简单对话"""
    start = time.time()
    try:
        system_prompt = "你是一个友好的助手，简短回答。"
        messages = [{"role": "user", "content": f"请用一句话介绍你自己（测试请求 #{index}）"}]
        response = generate_reply(system_prompt, messages)
        elapsed = time.time() - start
        print(f"✓ 请求 #{index} 成功 ({elapsed:.2f}s): {response[:50]}...")
        return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ 请求 #{index} 失败 ({elapsed:.2f}s): {e}")
        return False


def test_json_call(index: int):
    """测试 JSON 返回"""
    start = time.time()
    try:
        system_prompt = '你是助手，必须返回JSON格式: {"message": "你的回复", "index": 数字}'
        messages = [{"role": "user", "content": f"返回测试消息，index是{index}"}]
        response = call_llm_json(messages, system_prompt, reasoning_effort="low", timeout_seconds=30)
        elapsed = time.time() - start
        print(f"✓ JSON请求 #{index} 成功 ({elapsed:.2f}s): {response}")
        return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ JSON请求 #{index} 失败 ({elapsed:.2f}s): {e}")
        return False


def run_concurrent_test(num_requests: int = 10, test_type: str = "chat"):
    """运行并发测试"""
    print(f"\n{'='*60}")
    print(f"并发测试: {num_requests} 个请求")
    print(f"配置的 API keys 数量: {len(_api_keys)}")
    print(f"测试类型: {test_type}")
    print(f"{'='*60}\n")

    test_func = test_simple_chat if test_type == "chat" else test_json_call

    start_time = time.time()

    # 使用线程池并发请求
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(test_func, i) for i in range(1, num_requests + 1)]
        results = [f.result() for f in futures]

    elapsed = time.time() - start_time
    success_count = sum(results)

    print(f"\n{'='*60}")
    print(f"测试完成:")
    print(f"  总请求数: {num_requests}")
    print(f"  成功: {success_count}")
    print(f"  失败: {num_requests - success_count}")
    print(f"  总耗时: {elapsed:.2f}s")
    print(f"  平均响应时间: {elapsed/num_requests:.2f}s")
    print(f"  QPS: {num_requests/elapsed:.2f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # 检查配置
    if not _api_keys:
        print("❌ 错误: 未配置 API keys")
        sys.exit(1)

    print(f"✓ 已加载 {len(_api_keys)} 个 API key")
    for i, key in enumerate(_api_keys, 1):
        print(f"  Key {i}: {key[:20]}...")

    # 测试场景
    print("\n" + "="*60)
    print("选择测试场景:")
    print("  1. 轻量测试 (5个请求)")
    print("  2. 中等负载 (10个请求)")
    print("  3. 高负载 (20个请求)")
    print("  4. 压力测试 (50个请求)")
    print("  5. 自定义")
    print("="*60)

    try:
        choice = input("请选择 (1-5): ").strip()

        if choice == "1":
            run_concurrent_test(5, "chat")
        elif choice == "2":
            run_concurrent_test(10, "chat")
        elif choice == "3":
            run_concurrent_test(20, "chat")
        elif choice == "4":
            run_concurrent_test(50, "chat")
        elif choice == "5":
            num = int(input("请输入并发请求数: "))
            test_type = input("测试类型 (chat/json): ").strip() or "chat"
            run_concurrent_test(num, test_type)
        else:
            print("无效选择")

    except KeyboardInterrupt:
        print("\n\n测试被中断")
    except Exception as e:
        print(f"\n\n测试出错: {e}")
