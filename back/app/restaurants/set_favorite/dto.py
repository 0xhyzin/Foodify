from app.shared.dto import APIModel


class FavoriteRequest(APIModel):
    favorite: bool
