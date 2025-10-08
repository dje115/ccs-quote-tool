#!/usr/bin/env python3
"""
Pricing service that integrates web scraping with database caching.
"""

import json
from datetime import datetime, timedelta
from models import db, Supplier, SupplierPricing
from utils.web_pricing_scraper import WebPricingScraper
import logging

logger = logging.getLogger(__name__)

class PricingService:
    def __init__(self):
        self.scraper = WebPricingScraper()
        self.cache_duration = timedelta(hours=24)  # Cache pricing for 24 hours
    
    def get_product_price(self, supplier_name, product_name, force_refresh=False):
        """Get pricing for a product with caching"""
        try:
            # Clean inputs
            supplier_name = supplier_name.strip()
            product_name = product_name.strip()
            
            # Check if we have a cached price that's still valid
            if not force_refresh:
                cached_price = self._get_cached_price(supplier_name, product_name)
                if cached_price:
                    return cached_price
            
            # Try to get pricing from web scraper
            pricing_result = self.scraper.get_product_pricing(supplier_name, product_name)
            
            if pricing_result.get('success'):
                # Cache the result
                self._cache_price(supplier_name, product_name, pricing_result)
                return pricing_result
            else:
                # Return cached price even if expired, or None if no cache
                cached_price = self._get_cached_price(supplier_name, product_name, ignore_expiry=True)
                return cached_price
                
        except Exception as e:
            logger.error(f"Error getting product price: {e}")
            # Return cached price if available
            cached_price = self._get_cached_price(supplier_name, product_name, ignore_expiry=True)
            return cached_price
    
    def _get_cached_price(self, supplier_name, product_name, ignore_expiry=False):
        """Get cached price from database"""
        try:
            # Find supplier
            supplier = Supplier.query.filter(
                Supplier.name.ilike(f'%{supplier_name}%'),
                Supplier.is_active == True
            ).first()
            
            if not supplier:
                return None
            
            # Find cached pricing
            cached_pricing = SupplierPricing.query.filter(
                SupplierPricing.supplier_id == supplier.id,
                SupplierPricing.product_name.ilike(f'%{product_name}%'),
                SupplierPricing.is_active == True
            ).order_by(SupplierPricing.last_updated.desc()).first()
            
            if not cached_pricing:
                return None
            
            # Check if cache is still valid
            if not ignore_expiry:
                if datetime.utcnow() - cached_pricing.last_updated > self.cache_duration:
                    return None
            
            return {
                'success': True,
                'price': cached_pricing.price,
                'currency': cached_pricing.currency,
                'source': 'cached',
                'cached_at': cached_pricing.last_updated.isoformat(),
                'product_name': cached_pricing.product_name
            }
            
        except Exception as e:
            logger.error(f"Error getting cached price: {e}")
            return None
    
    def _cache_price(self, supplier_name, product_name, pricing_result):
        """Cache pricing result in database"""
        try:
            # Find supplier
            supplier = Supplier.query.filter(
                Supplier.name.ilike(f'%{supplier_name}%'),
                Supplier.is_active == True
            ).first()
            
            if not supplier:
                logger.warning(f"Supplier not found: {supplier_name}")
                return
            
            # Deactivate old cached entries for this product
            old_entries = SupplierPricing.query.filter(
                SupplierPricing.supplier_id == supplier.id,
                SupplierPricing.product_name.ilike(f'%{product_name}%')
            ).all()
            
            for entry in old_entries:
                entry.is_active = False
            
            # Create new cached entry
            cached_pricing = SupplierPricing(
                supplier_id=supplier.id,
                product_name=pricing_result.get('product_name', product_name),
                product_code=pricing_result.get('product_code', ''),
                price=pricing_result.get('price', 0),
                currency=pricing_result.get('currency', 'GBP'),
                is_active=True
            )
            
            db.session.add(cached_pricing)
            db.session.commit()
            
            logger.info(f"Cached pricing for {supplier_name} - {product_name}: £{pricing_result.get('price')}")
            
        except Exception as e:
            logger.error(f"Error caching price: {e}")
            db.session.rollback()
    
    def refresh_all_pricing(self):
        """Refresh pricing for all active suppliers"""
        try:
            suppliers = Supplier.query.filter_by(is_active=True, is_preferred=True).all()
            
            refreshed_count = 0
            for supplier in suppliers:
                # Get common products for this supplier category
                products = self._get_common_products_for_supplier(supplier)
                
                for product in products:
                    result = self.get_product_price(supplier.name, product, force_refresh=True)
                    if result and result.get('success'):
                        refreshed_count += 1
                        logger.info(f"Refreshed pricing for {supplier.name} - {product}")
            
            return {
                'success': True,
                'refreshed_count': refreshed_count,
                'message': f'Refreshed pricing for {refreshed_count} products'
            }
            
        except Exception as e:
            logger.error(f"Error refreshing all pricing: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_common_products_for_supplier(self, supplier):
        """Get common products for a supplier based on their category"""
        category_name = supplier.category.name.lower()
        
        common_products = {
            'wifi': [
                'U6-Pro Access Point',
                'U6-Lite Access Point',
                'U6-LR Access Point',
                'Dream Machine',
                'Dream Machine Pro'
            ],
            'cabling': [
                'Cat6 UTP Cable 305m',
                '24-port Cat6 Patch Panel',
                'RJ45 Keystone Jack',
                'Cat6 Face Plate'
            ],
            'cctv': [
                'G4 Pro Camera',
                'G4 Bullet Camera',
                'G4 Dome Camera',
                'NVR Pro'
            ],
            'door entry': [
                'Paxton Net2',
                'Comelit Video Door Entry',
                'BPT Intercom'
            ],
            'network equipment': [
                '24-port PoE Switch',
                '48-port Switch',
                'Router',
                'Firewall'
            ]
        }
        
        return common_products.get(category_name, [])
    
    def get_supplier_pricing_summary(self):
        """Get summary of cached pricing by supplier"""
        try:
            suppliers = Supplier.query.filter_by(is_active=True).all()
            summary = []
            
            for supplier in suppliers:
                cached_count = SupplierPricing.query.filter(
                    SupplierPricing.supplier_id == supplier.id,
                    SupplierPricing.is_active == True
                ).count()
                
                summary.append({
                    'supplier_name': supplier.name,
                    'category': supplier.category.name,
                    'cached_products': cached_count,
                    'is_preferred': supplier.is_preferred
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting pricing summary: {e}")
            return []



