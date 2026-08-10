import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/entities/menu_entities.dart';
import 'api_providers.dart';

final categoriesProvider = FutureProvider.autoDispose<List<CategoryEntity>>((ref) async {
  final menu = ref.watch(menuApiProvider);
  final categories = await menu.listCategories();
  final active = categories.where((c) => c.isActive).toList()
    ..sort((a, b) => a.displayOrder.compareTo(b.displayOrder));
  return active.map((dto) => dto.toEntity()).toList();
});

final productsProvider = FutureProvider.autoDispose<List<ProductEntity>>((ref) async {
  final menu = ref.watch(menuApiProvider);
  final products = await menu.listProducts();
  return products.where((p) => p.isActive).map((dto) => dto.toEntity()).toList();
});
