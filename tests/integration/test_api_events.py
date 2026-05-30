"""
事件API成测试
"""

import pytest
from datetime import datetime, timedelta


# API 路由前缀。若测试全部 404，去 app.py 看 include_router 的 prefix，改这里即可。
API = "/api"


class TestEventsAPI:
    """
    事件API测试类

    功能：测试事件管理API接口
    """

    def test_create_event(self, client):
        """
        测试创建事件API

        输入：
            client: 测试客户端夹具
        输出：无
        """
        resp = client.post(
            f"{API}/events",
            json={
                "title": "团队会议",
                "start_time": "2026-05-31T15:15:00",
                "reminder_minutes": 30,
            },
        )

        # 创建成功应返回 201，并带上自增 id 与正确字段
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] is not None
        assert data["title"] == "团队会议"
        assert data["reminder_minutes"] == 30
        assert datetime.fromisoformat(data["start_time"]) == datetime(2026, 5, 31, 15, 15)

    def test_get_events(self, client):
        """
        测试获取事件列表API

        输入：
            client: 测试客户端夹具
        输出：无
        """
        # 先通过接口创建两个事件
        client.post(f"{API}/events", json={"title": "会议A", "start_time": "2026-05-31T09:00:00"})
        client.post(f"{API}/events", json={"title": "会议B", "start_time": "2026-05-31T14:00:00"})

        # 不带日期 → 返回全部
        resp = client.get(f"{API}/events")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["events"]) == 2

    def test_delete_event(self, client):
        """
        测试删除事件API

        输入：
            client: 测试客户端夹具
        输出：无
        """
        # 先创建一个事件，拿到 id
        resp = client.post(f"{API}/events", json={"title": "待删除", "start_time": "2026-05-31T10:00:00"})
        event_id = resp.json()["id"]

        # 删除存在的事件 → 200
        resp = client.delete(f"{API}/events/{event_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == event_id

        # 再查应该查不到 → 404
        resp = client.get(f"{API}/events/{event_id}")
        assert resp.status_code == 404

        # 删除不存在的事件 → 404
        resp = client.delete(f"{API}/events/99999")
        assert resp.status_code == 404

    def test_update_event(self, client):
        """
        测试更新事件API

        输入：
            client: 测试客户端夹具
        输出：无
        """
        # 先创建一个事件
        resp = client.post(f"{API}/events", json={"title": "原标题", "start_time": "2026-05-31T09:00:00"})
        event_id = resp.json()["id"]

        # 更新存在的事件 → 200，标题已改
        resp = client.put(f"{API}/events/{event_id}", json={"title": "新标题"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "新标题"

        # 更新不存在的事件 → 404
        resp = client.put(f"{API}/events/99999", json={"title": "随便"})
        assert resp.status_code == 404