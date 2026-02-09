from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class TestJustDRFAPI(APITestCase):
    """
    适配你项目的路由：
    - 登录拿 JWT：POST /api/token/login/
    - 文章：/api/articles/  和 /api/articles/{id}/
    - 点赞：POST /api/articles/{id}/like/
    权限：IsAuthenticatedOrReadOnly + IsAuthorOrReadOnly
    """

    def setUp(self):
        # 创建两个用户：作者 & 非作者
        self.user1 = User.objects.create_user(username="u1", password="pass12345")
        self.user2 = User.objects.create_user(username="u2", password="pass12345")

    def login(self, username: str, password: str) -> str:
        """登录拿 JWT，并把 access token 写到后续请求的 Authorization header 里"""
        resp = self.client.post(
            "/api/token/login/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

        access = resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        return access

    def logout(self):
        """清掉 Authorization header（变回匿名）"""
        self.client.credentials()

    def test_01_login_get_jwt(self):
        resp = self.client.post(
            "/api/token/login/",
            {"username": "u1", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_02_article_crud(self):
        # 先登录为 u1（作者）
        self.login("u1", "pass12345")

        # Create：author 由后端自动指定，所以只传 title/body/status 即可
        create_resp = self.client.post(
            "/api/articles/",
            {"title": "t1", "body": "hello body", "status": "published"},
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED, create_resp.data)
        post_id = create_resp.data["id"]

        # List
        list_resp = self.client.get("/api/articles/")
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK, list_resp.data)
        self.assertIn("results", list_resp.data)  # 你的项目是分页返回

        # Detail（注意：你重写了 retrieve，会用到 Redis，所以 Redis 必须开着）
        detail_resp = self.client.get(f"/api/articles/{post_id}/")
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK, detail_resp.data)
        self.assertEqual(detail_resp.data["id"], post_id)

        # Patch（作者可改）
        patch_resp = self.client.patch(
            f"/api/articles/{post_id}/",
            {"title": "t1-updated"},
            format="json",
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK, patch_resp.data)
        self.assertEqual(patch_resp.data["title"], "t1-updated")

        # Delete（作者可删）
        del_resp = self.client.delete(f"/api/articles/{post_id}/")
        self.assertIn(del_resp.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK])

        # 再获取应 404
        detail_resp2 = self.client.get(f"/api/articles/{post_id}/")
        self.assertEqual(detail_resp2.status_code, status.HTTP_404_NOT_FOUND)

    def test_03_like_unlike_toggle(self):
        self.login("u1", "pass12345")

        # 建一篇文章
        create_resp = self.client.post(
            "/api/articles/",
            {"title": "like test", "body": "body", "status": "published"},
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED, create_resp.data)
        post_id = create_resp.data["id"]

        # 第一次 like
        like_resp = self.client.post(f"/api/articles/{post_id}/like/", format="json")
        self.assertEqual(like_resp.status_code, status.HTTP_200_OK, like_resp.data)
        self.assertIn("like_count", like_resp.data)
        self.assertEqual(like_resp.data["like_count"], 1)

        # 第二次 like => toggle 取消
        unlike_resp = self.client.post(f"/api/articles/{post_id}/like/", format="json")
        self.assertEqual(unlike_resp.status_code, status.HTTP_200_OK, unlike_resp.data)
        self.assertEqual(unlike_resp.data["like_count"], 0)

    def test_04_permission_non_author_cannot_update_or_delete(self):
        # u1 创建文章
        self.login("u1", "pass12345")
        create_resp = self.client.post(
            "/api/articles/",
            {"title": "owner post", "body": "body", "status": "published"},
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED, create_resp.data)
        post_id = create_resp.data["id"]

        # 切换到 u2（非作者）
        self.logout()
        self.login("u2", "pass12345")

        # u2 patch 应 403
        patch_resp = self.client.patch(
            f"/api/articles/{post_id}/",
            {"title": "hacked"},
            format="json",
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_403_FORBIDDEN, patch_resp.data)

        # u2 delete 应 403
        del_resp = self.client.delete(f"/api/articles/{post_id}/")
        self.assertEqual(del_resp.status_code, status.HTTP_403_FORBIDDEN)

# Create your tests here.
