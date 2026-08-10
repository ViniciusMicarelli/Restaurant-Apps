import '../../domain/entities/menu_entities.dart';

/// Espelha `CategoryResponse` do `menu-service`.
class CategoryDto {
  const CategoryDto({required this.id, required this.name, required this.displayOrder, required this.isActive});

  factory CategoryDto.fromJson(Map<String, dynamic> json) {
    return CategoryDto(
      id: json['id'] as String,
      name: json['name'] as String,
      displayOrder: json['display_order'] as int,
      isActive: json['is_active'] as bool,
    );
  }

  final String id;
  final String name;
  final int displayOrder;
  final bool isActive;

  CategoryEntity toEntity() => CategoryEntity(id: id, name: name, displayOrder: displayOrder);
}

/// Espelha `ProductResponse` do `menu-service`.
class ProductDto {
  const ProductDto({
    required this.id,
    required this.categoryId,
    required this.name,
    required this.description,
    required this.price,
    required this.photoUrl,
    required this.isActive,
  });

  factory ProductDto.fromJson(Map<String, dynamic> json) {
    return ProductDto(
      id: json['id'] as String,
      categoryId: json['category_id'] as String,
      name: json['name'] as String,
      description: json['description'] as String,
      price: (json['price'] as num).toDouble(),
      photoUrl: json['photo_url'] as String,
      isActive: json['is_active'] as bool,
    );
  }

  final String id;
  final String categoryId;
  final String name;
  final String description;
  final double price;
  final String photoUrl;
  final bool isActive;

  ProductEntity toEntity() => ProductEntity(
    id: id,
    categoryId: categoryId,
    name: name,
    description: description,
    price: price,
    photoUrl: photoUrl,
  );
}
