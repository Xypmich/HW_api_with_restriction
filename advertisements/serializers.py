import rest_framework.request
from django.contrib.auth.models import User
from rest_framework import serializers

from advertisements.models import Advertisement


class UserSerializer(serializers.ModelSerializer):
    """Serializer для пользователя."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name',)


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для объявления."""

    creator = UserSerializer(
        read_only=True,
    )

    class Meta:
        model = Advertisement
        fields = ('id', 'title', 'description', 'creator',
                  'status', 'created_at', )

    def create(self, validated_data):
        """Метод для создания"""

        # Простановка значения поля создатель по-умолчанию.
        # Текущий пользователь является создателем объявления
        # изменить или переопределить его через API нельзя.
        # обратите внимание на `context` – он выставляется автоматически
        # через методы ViewSet.
        # само поле при этом объявляется как `read_only=True`
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        """Метод для валидации. Вызывается при создании и обновлении."""
        request_token = self.context['request'].auth
        request_method = self.context['request'].method
        adv_count = len(Advertisement.objects.filter(
            creator=self.context['request'].user,
            status='OPEN'
        ))
        if request_method == 'POST' and adv_count >= 10:
            raise serializers.ValidationError(
                'You have reached maximum limit of open advertisements (10/10). '
                'Please, close or delete at least one advertisement'
            )
        elif request_method == 'PATCH':
            adv_number = int(self.context['request'].parser_context['kwargs']['pk'])
            adv_creator = Advertisement.objects.get(id=adv_number).creator
            if not request_token == adv_creator.auth_token:
                raise serializers.ValidationError(
                    'No permissions to change: Advertisement not created by current user.'
                )
            elif data['status'] == 'OPEN' and adv_count >= 10:
                raise serializers.ValidationError(
                    'You have reached maximum limit of open advertisements (10/10). '
                    'Please, close or delete at least one advertisement'
                )
        return data
