import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCard } from './ProductCard';
import type { Product } from '../../../domain/entities/product';

const product: Product = {
  id: 'prod-1',
  category_id: 'cat-1',
  name: 'X-Burger',
  description: 'Hambúrguer artesanal',
  price: 25.5,
  photo_url: 'https://example.com/photo.jpg',
  is_active: true,
};

describe('ProductCard', () => {
  it('renders the product name, description and formatted price', () => {
    render(<ProductCard product={product} onAddToCart={vi.fn()} />);

    expect(screen.getByText('X-Burger')).toBeInTheDocument();
    expect(screen.getByText('Hambúrguer artesanal')).toBeInTheDocument();
    expect(screen.getByText('R$ 25,50')).toBeInTheDocument();
  });

  it('calls onAddToCart with the product id and name when clicked', () => {
    const onAddToCart = vi.fn();
    render(<ProductCard product={product} onAddToCart={onAddToCart} />);

    fireEvent.click(screen.getByRole('button', { name: /adicionar/i }));

    expect(onAddToCart).toHaveBeenCalledWith('prod-1', 'X-Burger');
  });
});
