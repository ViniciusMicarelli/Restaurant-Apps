/// Restaurante + branding White-Label — espelha `RestaurantResponse` do
/// `restaurant-service` (só os campos consumidos pelo app do cliente).
class RestaurantEntity {
  const RestaurantEntity({
    required this.id,
    required this.slug,
    required this.tradeName,
    required this.primaryColor,
    required this.logoUrl,
    required this.bannerUrl,
  });

  final String id;
  final String slug;
  final String tradeName;
  final String primaryColor;
  final String logoUrl;
  final String bannerUrl;
}
