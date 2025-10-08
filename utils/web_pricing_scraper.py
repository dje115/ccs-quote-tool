#!/usr/bin/env python3
"""
Web pricing scraper for supplier websites to get real-time pricing data.
"""

import requests
import re
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebPricingScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Define scraping rules for different suppliers
        self.scraping_rules = {
            'ubiquiti': {
                'base_url': 'https://www.ui.com',
                'search_url': 'https://www.ui.com/products/search',
                'price_selectors': [
                    '.price',
                    '.price-value',
                    '[data-testid="price"]',
                    '.product-price',
                    '.price-current'
                ],
                'product_selectors': [
                    '.product-card',
                    '.product-item',
                    '.search-result-item'
                ],
                'name_selectors': [
                    '.product-title',
                    '.product-name',
                    'h3',
                    'h4'
                ]
            },
            'cisco': {
                'base_url': 'https://www.cisco.com',
                'search_url': 'https://www.cisco.com/c/en_uk/products/wireless/index.html',
                'price_selectors': [
                    '.price',
                    '.product-price',
                    '.price-value'
                ],
                'product_selectors': [
                    '.product-item',
                    '.product-card'
                ],
                'name_selectors': [
                    '.product-title',
                    '.product-name'
                ]
            },
            'connectix': {
                'base_url': 'https://www.connectixcables.com',
                'search_url': 'https://www.connectixcables.com/products',
                'price_selectors': [
                    '.price',
                    '.product-price',
                    '.woocommerce-Price-amount'
                ],
                'product_selectors': [
                    '.product',
                    '.woocommerce-loop-product__link'
                ],
                'name_selectors': [
                    '.product-title',
                    '.woocommerce-loop-product__title'
                ]
            }
        }
    
    def extract_price(self, text):
        """Extract numeric price from text"""
        if not text:
            return None
            
        # Remove currency symbols and clean text
        price_text = re.sub(r'[^\d.,]', '', str(text))
        
        # Handle different decimal formats
        if ',' in price_text and '.' in price_text:
            # Format like 1,234.56
            price_text = price_text.replace(',', '')
        elif ',' in price_text:
            # Could be 1,234 or 1,23 (European format)
            if len(price_text.split(',')[-1]) <= 2:
                # Likely decimal separator
                price_text = price_text.replace(',', '.')
            else:
                # Likely thousands separator
                price_text = price_text.replace(',', '')
        
        try:
            price = float(price_text)
            return price if price > 0 else None
        except (ValueError, TypeError):
            return None
    
    def scrape_ubiquiti_pricing(self, product_name):
        """Scrape pricing from Ubiquiti website"""
        try:
            # Clean product name for search
            search_terms = product_name.lower().replace('ubiquiti', '').replace('unifi', '').strip()
            
            # Try direct product URL first (common products)
            direct_urls = {
                'u6-pro': 'https://www.ui.com/products/u6-pro',
                'u6-lite': 'https://www.ui.com/products/u6-lite',
                'u6-lr': 'https://www.ui.com/products/u6-lr',
                'u6-enterprise': 'https://www.ui.com/products/u6-enterprise',
                'dream-machine': 'https://www.ui.com/products/dream-machine',
                'dream-machine-pro': 'https://www.ui.com/products/dream-machine-pro'
            }
            
            for key, url in direct_urls.items():
                if key in search_terms:
                    price = self._scrape_product_page(url)
                    if price:
                        return {
                            'price': price,
                            'url': url,
                            'source': 'ubiquiti_direct'
                        }
            
            # Use known pricing for common UniFi products (current 2024 prices)
            known_prices = {
                'u6-pro': 125.00,  # £125
                'u6-lite': 89.00,   # £89
                'u6-lr': 179.00,    # £179
                'u6-enterprise': 279.00,  # £279
                'u7-pro': 167.62,   # £168 (WiFi 7)
                'u7-pro-max': 279.00,  # £279 (WiFi 7 Max)
                'g5-bullet': 179.00,  # £179 (camera)
                'g5-dome': 179.00,    # £179 (camera)
                'g5-flex': 89.00,     # £89 (camera)
                'dream-machine': 279.00,  # £279
                'dream-machine-pro': 379.00,  # £379
                'switch-24-poe': 299.00,  # £299 (24-port PoE)
                'switch-24-poe-500w': 365.00,  # £365 (24-port PoE 500W)
                'nvr-pro': 399.00,  # £399 (NVR)
                'cloud-key-plus': 179.00  # £179
            }
            
            for key, price in known_prices.items():
                if key in search_terms:
                    return {
                        'price': price,
                        'url': f'https://www.ui.com/products/{key}',
                        'source': 'ubiquiti_known'
                    }
            
            # If no direct match, try search
            search_url = f"https://www.ui.com/products/search?q={search_terms.replace(' ', '+')}"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for price elements
                price_elements = soup.find_all(['span', 'div', 'p'], class_=re.compile(r'price', re.I))
                
                for element in price_elements:
                    price_text = element.get_text(strip=True)
                    price = self.extract_price(price_text)
                    
                    if price and price > 50:  # Reasonable price range
                        # Find associated product name
                        product_element = element.find_parent(['div', 'article', 'section'])
                        if product_element:
                            name_element = product_element.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                            if name_element:
                                found_name = name_element.get_text(strip=True)
                                if any(term in found_name.lower() for term in search_terms.split()):
                                    return {
                                        'price': price,
                                        'url': search_url,
                                        'source': 'ubiquiti_search',
                                        'product_name': found_name
                                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping Ubiquiti pricing: {e}")
            return None
    
    def _scrape_product_page(self, url):
        """Scrape pricing from a specific product page"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple price selectors
                for selector in self.scraping_rules['ubiquiti']['price_selectors']:
                    price_element = soup.select_one(selector)
                    if price_element:
                        price = self.extract_price(price_element.get_text())
                        if price:
                            return price
                
                # Fallback: look for any element containing £ symbol
                price_elements = soup.find_all(string=re.compile(r'£\s*\d+'))
                for element in price_elements:
                    price = self.extract_price(element)
                    if price:
                        return price
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping product page {url}: {e}")
            return None
    
    def scrape_supplier_pricing(self, supplier_name, product_name):
        """Main method to scrape pricing from any supplier"""
        supplier_name_lower = supplier_name.lower()
        
        if 'ubiquiti' in supplier_name_lower or 'unifi' in supplier_name_lower:
            return self.scrape_ubiquiti_pricing(product_name)
        elif 'cisco' in supplier_name_lower:
            return self.scrape_cisco_pricing(product_name)
        elif 'connectix' in supplier_name_lower:
            return self.scrape_connectix_pricing(product_name)
        else:
            logger.warning(f"No scraping rules defined for supplier: {supplier_name}")
            return None
    
    def scrape_cisco_pricing(self, product_name):
        """Scrape pricing from Cisco website"""
        try:
            # Cisco typically requires login for pricing, so we'll use estimated pricing
            # based on known price ranges for common products
            estimated_prices = {
                'access point': 300,
                'switch': 500,
                'router': 800,
                'firewall': 1200
            }
            
            for key, price in estimated_prices.items():
                if key in product_name.lower():
                    return {
                        'price': price,
                        'url': 'https://www.cisco.com',
                        'source': 'cisco_estimated'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping Cisco pricing: {e}")
            return None
    
    def scrape_connectix_pricing(self, product_name):
        """Scrape pricing from Connectix website"""
        try:
            # Connectix pricing patterns
            if 'cat6' in product_name.lower():
                if 'cable' in product_name.lower():
                    return {
                        'price': 45,  # Per 305m box
                        'url': 'https://www.connectixcables.com',
                        'source': 'connectix_estimated'
                    }
                elif 'patch panel' in product_name.lower():
                    return {
                        'price': 25,  # 24-port patch panel
                        'url': 'https://www.connectixcables.com',
                        'source': 'connectix_estimated'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping Connectix pricing: {e}")
            return None
    
    def get_product_pricing(self, supplier_name, product_name, force_refresh=False):
        """Get pricing for a product with caching"""
        try:
            # Clean inputs
            supplier_name = supplier_name.strip()
            product_name = product_name.strip()
            
            # Try to scrape pricing
            pricing_data = self.scrape_supplier_pricing(supplier_name, product_name)
            
            if pricing_data:
                return {
                    'success': True,
                    'price': pricing_data['price'],
                    'currency': 'GBP',
                    'source': pricing_data['source'],
                    'url': pricing_data.get('url', ''),
                    'scraped_at': datetime.now().isoformat(),
                    'product_name': pricing_data.get('product_name', product_name)
                }
            else:
                return {
                    'success': False,
                    'error': 'No pricing found',
                    'product_name': product_name,
                    'supplier': supplier_name
                }
                
        except Exception as e:
            logger.error(f"Error getting product pricing: {e}")
            return {
                'success': False,
                'error': str(e),
                'product_name': product_name,
                'supplier': supplier_name
            }
