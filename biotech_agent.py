#!/usr/bin/env python3
"""
Biotech & Pharma Monthly News Agent
Runs automatically via GitHub Actions
"""

import feedparser
import pandas as pd
from datetime import datetime, timedelta
import re
import os

class BiotechNewsAgent:
    def __init__(self):
        # Free RSS feeds - no API keys needed!
        self.feeds = {
            'FierceBiotech': 'https://www.fiercebiotech.com/rss/xml',
            'BioPharma Dive': 'https://www.biopharmadive.com/feeds/news/',
            'GEN News': 'https://www.genengnews.com/feed/',
            'BioSpace': 'https://www.biospace.com/feed/',
        }
        
        # Keywords for categorization
        self.keywords = {
            'revenue': ['revenue', 'earnings', 'quarterly results', 'q1', 'q2', 'q3', 'q4', 
                       'sales', 'financial results', 'profit'],
            'acquisition': ['acquisition', 'merger', 'acquire', 'acquired', 'deal', 'bought',
                          'takeover', 'm&a', 'purchase'],
            'funding': ['funding', 'raised', 'series a', 'series b', 'series c', 'investment',
                       'investors', 'venture capital', 'ipo', 'financing'],
            'new_company': ['launched', 'founded', 'new company', 'startup', 'spin-off',
                          'spinout', 'established', 'announces formation']
        }
        
    def fetch_news_from_feed(self, feed_url, source_name, days_back=30):
        """Fetch articles from a single RSS feed"""
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            print(f"  Fetching from {source_name}...")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:100]:  # Last 100 articles
                articles.append({
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', ''),
                    'source': source_name
                })
            
            print(f"    ✓ Found {len(articles)} articles")
            
        except Exception as e:
            print(f"    ✗ Error fetching from {source_name}: {e}")
        
        return articles
    
    def fetch_all_news(self, days_back=30):
        """Fetch news from all RSS feeds"""
        print("\n" + "="*60)
        print("COLLECTING NEWS FROM SOURCES")
        print("="*60)
        
        all_articles = []
        
        for source_name, feed_url in self.feeds.items():
            articles = self.fetch_news_from_feed(feed_url, source_name, days_back)
            all_articles.extend(articles)
        
        print(f"\n✓ Total articles collected: {len(all_articles)}")
        return all_articles
    
    def categorize_article(self, article):
        """Determine which categories an article belongs to"""
        text = (article['title'] + ' ' + article['summary']).lower()
        
        categories = []
        for category, keywords in self.keywords.items():
            if any(keyword in text for keyword in keywords):
                categories.append(category)
        
        return categories
    
    def extract_company_name(self, text):
        """Try to extract company name from title (simple heuristic)"""
        # Look for capitalized words at the start
        words = text.split()
        company_words = []
        
        for word in words[:5]:  # Check first 5 words
            if word[0].isupper() and len(word) > 2:
                company_words.append(word)
            else:
                break
        
        return ' '.join(company_words) if company_words else 'Unknown'
    
    def process_articles(self, articles):
        """Categorize and organize articles"""
        print("\n" + "="*60)
        print("PROCESSING AND CATEGORIZING ARTICLES")
        print("="*60)
        
        categorized = {
            'revenue': [],
            'acquisitions': [],
            'funding': [],
            'new_companies': []
        }
        
        for article in articles:
            categories = self.categorize_article(article)
            
            # Extract basic info
            company = self.extract_company_name(article['title'])
            
            data = {
                'Company': company,
                'Date': article['published'][:10] if article['published'] else 'N/A',
                'Title': article['title'],
                'Source': article['source'],
                'URL': article['link'],
                'Summary': article['summary'][:200] + '...' if len(article['summary']) > 200 else article['summary']
            }
            
            # Add to appropriate categories
            if 'revenue' in categories:
                categorized['revenue'].append(data)
            if 'acquisition' in categories:
                categorized['acquisitions'].append(data)
            if 'funding' in categories:
                categorized['funding'].append(data)
            if 'new_company' in categories:
                categorized['new_companies'].append(data)
        
        # Print summary
        print(f"\n✓ Revenue articles: {len(categorized['revenue'])}")
        print(f"✓ Acquisition articles: {len(categorized['acquisitions'])}")
        print(f"✓ Funding articles: {len(categorized['funding'])}")
        print(f"✓ New company articles: {len(categorized['new_companies'])}")
        
        return categorized
    
    def create_excel_report(self, categorized_data):
        """Generate Excel report with multiple sheets"""
        print("\n" + "="*60)
        print("GENERATING EXCEL REPORT")
        print("="*60)
        
        month_year = datetime.now().strftime('%Y-%m')
        filename = f'Biotech_Pharma_Report_{month_year}.xlsx'
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            
            # Summary Sheet
            summary_data = {
                'Category': ['Revenue Reports', 'Acquisitions', 'Funding Rounds', 'New Companies', 'Total Articles'],
                'Count': [
                    len(categorized_data['revenue']),
                    len(categorized_data['acquisitions']),
                    len(categorized_data['funding']),
                    len(categorized_data['new_companies']),
                    sum(len(v) for v in categorized_data.values())
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Individual category sheets
            for category, articles in categorized_data.items():
                if articles:
                    df = pd.DataFrame(articles)
                    sheet_name = category.replace('_', ' ').title()
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Metadata sheet
            metadata = {
                'Field': ['Report Generated', 'Report Period', 'Sources Used', 'Agent Version'],
                'Value': [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                    datetime.now().strftime('%B %Y'),
                    ', '.join(self.feeds.keys()),
                    '1.0.0 (GitHub Actions)'
                ]
            }
            df_metadata = pd.DataFrame(metadata)
            df_metadata.to_excel(writer, sheet_name='Metadata', index=False)
        
        print(f"\n✓ Excel report created: {filename}")
        return filename
    
    def run_monthly_report(self, days_back=30):
        """Main execution method"""
        print("\n" + "="*70)
        print(" "*15 + "BIOTECH & PHARMA NEWS AGENT")
        print(" "*20 + "Automated Monthly Report")
        print("="*70)
        print(f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Looking back: {days_back} days")
        print("="*70)
        
        # Step 1: Collect news
        articles = self.fetch_all_news(days_back)
        
        if not articles:
            print("\n⚠ Warning: No articles collected. Check RSS feeds.")
            return None
        
        # Step 2: Process and categorize
        categorized = self.process_articles(articles)
        
        # Step 3: Create Excel report
        filename = self.create_excel_report(categorized)
        
        print("\n" + "="*70)
        print(" "*25 + "REPORT COMPLETE!")
        print("="*70)
        
        return filename


# Main execution
if __name__ == "__main__":
    agent = BiotechNewsAgent()
    report_file = agent.run_monthly_report(days_back=30)
    
    if report_file:
        print(f"\n📊 Report ready: {report_file}")
        print("\n✉️  Report will be emailed to you automatically")
    else:
        print("\n❌ Report generation failed")
