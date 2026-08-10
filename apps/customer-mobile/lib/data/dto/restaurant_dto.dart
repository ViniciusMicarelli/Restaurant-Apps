import '../../domain/entities/restaurant_entity.dart';

/// Espelha `RestaurantResponse` (com `branding` aninhado) do `restaurant-service`.
class RestaurantDto {
  const RestaurantDto({
    required this.id,
    required this.slug,
    required this.tradeName,
    required this.primaryColor,
    required this.logoUrl,
    required this.bannerUrl,
  });

  factory RestaurantDto.fromJson(Map<String, dynamic> json) {
    final branding = json['branding'] as Map<String, dynamic>;
    return RestaurantDto(
      id: json['id'] as String,
      slug: json['slug'] as String,
      tradeName: json['trade_name'] as String,
      primaryColor: branding['primary_color'] as String,
      logoUrl: branding['logo_url'] as String,
      bannerUrl: branding['banner_url'] as String,
    );
  }

  final String id;
  final String slug;
  final String tradeName;
  final String primaryColor;
  final String logoUrl;
  final String bannerUrl;

  RestaurantEntity toEntity() => RestaurantEntity(
    id: id,
    slug: slug,
    tradeName: tradeName,
    primaryColor: primaryColor,
    logoUrl: logoUrl,
    bannerUrl: bannerUrl,
  );
}
