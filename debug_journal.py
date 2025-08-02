#!/usr/bin/env python3
"""Debug script to find the correct journal page format."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from logseq_mcp_server.logseq.client import LogseqClient
from logseq_mcp_server.utils.date_converter import date_to_journal_format
from logseq_mcp_server.utils.date_converter_extended import try_multiple_journal_formats
import os
from dotenv import load_dotenv

load_dotenv("env/.env")


async def debug_journal_format():
    """Test different journal formats to find what works."""
    client = LogseqClient(
        host=os.getenv("LOGSEQ_API_HOST", "localhost"),
        port=int(os.getenv("LOGSEQ_API_PORT", "12315")),
        token=os.getenv("LOGSEQ_API_TOKEN")
    )
    
    # Test date
    test_date = "2025-08-01"
    
    print(f"\n🔍 Debugging journal format for date: {test_date}")
    print("=" * 50)
    
    # Try multiple formats
    formats_to_try = [
        "August 1st, 2025",     # Full month
        "Aug 1st, 2025",        # Abbreviated
        "2025-08-01",           # ISO
        "08/01/2025",           # US format
        "2025_08_01",           # Underscore format
        "2025/08/01",           # Slash ISO
        "August 01, 2025",      # Zero-padded
        "Aug 01, 2025",         # Zero-padded abbreviated
    ]
    
    # Also try generated formats
    generated = try_multiple_journal_formats(test_date)
    formats_to_try.extend(generated)
    
    # Remove duplicates
    formats_to_try = list(dict.fromkeys(formats_to_try))
    
    for format_name in formats_to_try:
        print(f"\n📝 Trying format: '{format_name}'")
        try:
            page = await client.get_page(format_name)
            if page:
                print(f"✅ FOUND! Page exists with format: '{format_name}'")
                print(f"   UUID: {page.get('uuid')}")
                print(f"   Original name: {page.get('originalName')}")
                
                # Try to get blocks
                blocks = await client.get_page_blocks(format_name)
                print(f"   Blocks found: {len(blocks)}")
                if blocks:
                    print(f"   First block preview: {str(blocks[0])[:100]}...")
                    
                return format_name
            else:
                print(f"❌ Not found with this format")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n\n💡 Tip: Check your Logseq journal format settings!")
    print("You can also list all pages to see the exact format:")
    print("\n📋 Listing journal pages...")
    
    try:
        all_pages = await client.get_all_pages()
        journal_pages = [p for p in all_pages if p.get("journal?", False)][:10]
        
        if journal_pages:
            print("\nFound journal pages with these formats:")
            for page in journal_pages:
                print(f"  - {page.get('originalName', page.get('name'))}")
        else:
            print("No journal pages found!")
    except Exception as e:
        print(f"Error listing pages: {e}")
    
    await client.close()


if __name__ == "__main__":
    print("🚀 Logseq Journal Format Debugger")
    asyncio.run(debug_journal_format())