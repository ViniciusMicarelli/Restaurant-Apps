/// Categoria do cardápio — espelha `CategoryResponse` do `menu-service`.
class CategoryEntity {
  const CategoryEntity({required this.id, required this.name, required this.displayOrder});

  final String id;
  final String name;
  final int displayOrder;
}

/// Produto do cardápio — espelha `ProductResponse` do `menu-service`.
class ProductEntity {
  const ProductEntity({
    required this.id,
    required this.categoryId,
    required this.name,
    required this.description,
    required this.price,
    required this.photoUrl,
  });

  final String id;
  final String categoryId;
  final String name;
  final String description;
  final double price;
  final String photoUrl;
}
