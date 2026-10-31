from app.shared.dto import APIModel


class FavoritesData(APIModel):
    restaurant_ids: list[str]


class FavoritesResponse(APIModel):
    data: FavoritesData
