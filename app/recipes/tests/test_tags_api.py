from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipes.serializers import TagSerializer

TAGS_URL = reverse('recipes:tag-list')


class PublicTagsApi(TestCase):
    """ Test the publicly available tags API """

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """ Test that login is required for retrieving tags """
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApi(TestCase):
    """ Test authorized user tags API """

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@test.com',
            password='Test123',
            name="Test"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """ Test retrieving tags """
        Tag.objects.create(user=self.user, name="Main")
        Tag.objects.create(user=self.user, name="Sweets")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """ Test that tags return the authenitacated user """
        user2 = get_user_model().objects.create_user(
            email='test2@test.com',
            password='Test1234',
            name="Test2"
        )
        Tag.objects.create(user=user2, name="Italian")
        tag = Tag.objects.create(user=self.user, name="American")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_created_tags_succesful(self):
        """ Test creating a new tag"""
        payload = {'name': 'Test tag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_created_tags_invalid(self):
        """ Test creating a new tag with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)
