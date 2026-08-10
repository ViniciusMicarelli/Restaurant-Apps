import { afterEach, describe, expect, it } from 'vitest';
import { resolveRestaurantSlug, resolveTableNumber } from './restaurantSlug';

function setUrl(search: string) {
  window.history.pushState({}, '', `/${search}`);
}

afterEach(() => {
  setUrl('');
});

describe('resolveRestaurantSlug', () => {
  it('reads the slug from the "r" query parameter', () => {
    setUrl('?r=burger-house');
    expect(resolveRestaurantSlug()).toBe('burger-house');
  });

  it('returns null when there is no query parameter and no env default', () => {
    setUrl('');
    expect(resolveRestaurantSlug()).toBeNull();
  });
});

describe('resolveTableNumber', () => {
  it('parses the "table" query parameter as a number', () => {
    setUrl('?table=12');
    expect(resolveTableNumber()).toBe(12);
  });

  it('returns null when the table parameter is absent', () => {
    setUrl('?r=burger-house');
    expect(resolveTableNumber()).toBeNull();
  });

  it('returns null when the table parameter is not a valid number', () => {
    setUrl('?table=abc');
    expect(resolveTableNumber()).toBeNull();
  });
});
