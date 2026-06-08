from django.core.cache import cache

PRODUCT_LIST_CACHE_KEY = "products:list:default"
PRODUCT_LIST_CACHE_TTL = 60 * 3  # 3 phút

def is_only_get_list(payload) -> bool:
    return (
        not getattr(payload, "search", None)
        and not getattr(payload, "brand", None)
        and getattr(payload, "min_price", None) is None
        and getattr(payload, "max_price", None) is None
        and getattr(payload, "sort", "asc") == "asc"
    )

def clear_product_cache() -> None:
    cache.delete(PRODUCT_LIST_CACHE_KEY)