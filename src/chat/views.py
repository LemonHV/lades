from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def private_chat(request, user_uid):
    other_user = get_object_or_404(User, uid=user_uid)

    user1 = str(request.user.uid)
    user2 = str(other_user.uid)

    # đảm bảo room không bị đảo
    room_name = f"room_{min(user1, user2)}_{max(user1, user2)}"

    return render(request, "chat/room.html", {
        "room_name": room_name,
        "other_user": other_user
    })