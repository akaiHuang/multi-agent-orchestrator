"""
Dcard Research Storage - 將 Dcard 內容研究資料存儲到 Firebase
用於「充電小世界」行銷活動的內容研究數據
"""

from __future__ import annotations
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    _FIREBASE_AVAILABLE = True
except ImportError:
    firebase_admin = None
    credentials = None
    firestore = None
    _FIREBASE_AVAILABLE = False


class DcardResearchStorage:
    """Dcard 內容研究資料存儲器"""
    
    def __init__(self, service_account_path: Optional[str] = None):
        """
        初始化 Firebase 連接
        
        Args:
            service_account_path: Firebase 服務帳戶 JSON 路徑
        """
        if not _FIREBASE_AVAILABLE:
            raise RuntimeError("firebase-admin 未安裝。請執行: pip install firebase-admin")
        
        # 自動尋找服務帳戶檔案
        if service_account_path is None:
            # 嘗試從專案根目錄找
            project_root = Path(__file__).parent.parent.parent
            possible_paths = [
                project_root / "fir-js-61ce8-firebase-adminsdk-7fj5i-e6525c9c0b.json",
                Path(os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")),
            ]
            for path in possible_paths:
                if path.exists():
                    service_account_path = str(path)
                    break
        
        if not service_account_path or not Path(service_account_path).exists():
            raise FileNotFoundError("找不到 Firebase 服務帳戶檔案")
        
        # 初始化 Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        self.collection_name = "dcard_research"
        self.campaign_id = "charging_world"  # 充電小世界活動
        
    def save_keyword_research(self, keyword: str, data: dict) -> str:
        """
        儲存單一關鍵字的研究資料
        
        Args:
            keyword: 搜尋關鍵字
            data: 研究資料
            
        Returns:
            文件 ID
        """
        doc_ref = self.db.collection(self.collection_name).document(f"{self.campaign_id}_{keyword}")
        
        research_data = {
            "keyword": keyword,
            "campaign_id": self.campaign_id,
            "campaign_name": "充電小世界",
            "article_count": data.get("article_count", 0),
            "followers": data.get("followers", 0),
            "related_topics": data.get("related_topics", []),
            "related_boards": data.get("related_boards", []),
            "hot_articles": data.get("hot_articles", []),
            "related_searches": data.get("related_searches", []),
            "scraped_at": datetime.now(),
            "source": "dcard",
            "metadata": data.get("metadata", {})
        }
        
        doc_ref.set(research_data, merge=True)
        print(f"✅ 已儲存關鍵字研究: {keyword}")
        return doc_ref.id
    
    def save_all_research(self, research_results: list[dict]) -> dict:
        """
        批次儲存所有研究資料
        
        Args:
            research_results: 研究結果列表
            
        Returns:
            儲存結果統計
        """
        batch = self.db.batch()
        saved_count = 0
        
        for result in research_results:
            keyword = result.get("keyword")
            if not keyword:
                continue
                
            doc_ref = self.db.collection(self.collection_name).document(f"{self.campaign_id}_{keyword}")
            
            research_data = {
                "keyword": keyword,
                "campaign_id": self.campaign_id,
                "campaign_name": "充電小世界",
                "article_count": result.get("article_count", 0),
                "followers": result.get("followers", 0),
                "related_topics": result.get("related_topics", []),
                "related_boards": result.get("related_boards", []),
                "hot_articles": result.get("hot_articles", []),
                "related_searches": result.get("related_searches", []),
                "scraped_at": datetime.now(),
                "source": "dcard",
                "metadata": result.get("metadata", {})
            }
            
            batch.set(doc_ref, research_data, merge=True)
            saved_count += 1
        
        # 提交批次寫入
        batch.commit()
        
        # 儲存研究摘要
        self._save_research_summary(research_results)
        
        print(f"✅ 批次儲存完成: {saved_count} 筆關鍵字研究")
        return {"saved_count": saved_count, "campaign_id": self.campaign_id}
    
    def _save_research_summary(self, research_results: list[dict]):
        """儲存研究摘要"""
        total_articles = sum(r.get("article_count", 0) for r in research_results)
        
        summary = {
            "campaign_id": self.campaign_id,
            "campaign_name": "充電小世界",
            "campaign_tagline": "手機有充電的地方，你呢？",
            "total_keywords": len(research_results),
            "total_articles": total_articles,
            "keywords_searched": [r.get("keyword") for r in research_results],
            "research_date": datetime.now(),
            "source": "dcard",
            "status": "completed"
        }
        
        doc_ref = self.db.collection(self.collection_name).document(f"{self.campaign_id}_summary")
        doc_ref.set(summary, merge=True)
        print(f"✅ 已儲存研究摘要: 共 {total_articles:,} 篇文章")
    
    def save_hot_article(self, article: dict) -> str:
        """
        儲存高互動文章
        
        Args:
            article: 文章資料
            
        Returns:
            文件 ID
        """
        # 使用文章標題的 hash 作為 ID
        import hashlib
        title = article.get("title", "")
        article_id = hashlib.md5(title.encode()).hexdigest()[:12]
        
        doc_ref = self.db.collection(f"{self.collection_name}_articles").document(article_id)
        
        article_data = {
            "title": title,
            "board": article.get("board", ""),
            "reactions": article.get("reactions", 0),
            "comments": article.get("comments", 0),
            "saves": article.get("saves", 0),
            "preview": article.get("preview", ""),
            "url": article.get("url", ""),
            "posted_at": article.get("posted_at", ""),
            "keywords": article.get("keywords", []),
            "campaign_id": self.campaign_id,
            "scraped_at": datetime.now(),
            "source": "dcard"
        }
        
        doc_ref.set(article_data, merge=True)
        return doc_ref.id
    
    def get_research_by_keyword(self, keyword: str) -> Optional[dict]:
        """取得特定關鍵字的研究資料"""
        doc_ref = self.db.collection(self.collection_name).document(f"{self.campaign_id}_{keyword}")
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    
    def get_all_research(self) -> list[dict]:
        """取得所有研究資料"""
        docs = self.db.collection(self.collection_name).where(
            "campaign_id", "==", self.campaign_id
        ).stream()
        return [doc.to_dict() for doc in docs]
    
    def get_research_summary(self) -> Optional[dict]:
        """取得研究摘要"""
        doc_ref = self.db.collection(self.collection_name).document(f"{self.campaign_id}_summary")
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None


def save_charging_world_research():
    """
    儲存「充電小世界」活動的 Dcard 研究資料
    """
    storage = DcardResearchStorage()
    
    # 研究資料 - 從爬蟲結果整理
    research_results = [
        {
            "keyword": "焦慮",
            "article_count": 12184,
            "followers": 0,
            "related_topics": ["考試焦慮", "社交焦慮", "分離焦慮", "焦慮症"],
            "related_boards": ["心情", "感情", "心理", "女孩"],
            "hot_articles": [
                {"title": "女友薪水是我的三倍", "reactions": 1949, "board": "感情"},
                {"title": "台灣成最不想生國家第一名", "reactions": 1086, "board": "閒聊"},
            ],
            "related_searches": ["焦慮症", "考試焦慮", "社交焦慮"],
            "metadata": {"search_date": "2026-01-25"}
        },
        {
            "keyword": "好累",
            "article_count": 2049,
            "followers": 0,
            "related_topics": ["活著好累", "心好累", "上班好累"],
            "related_boards": ["心情", "工作", "感情"],
            "hot_articles": [
                {"title": "活著好累", "reactions": 500, "board": "心情"},
            ],
            "related_searches": ["活著好累", "心好累", "上班好累"],
            "metadata": {"search_date": "2026-01-25"}
        },
        {
            "keyword": "療癒",
            "article_count": 2715,
            "followers": 88,
            "related_topics": ["每日療癒小語", "療癒小物", "療癒系"],
            "related_boards": ["三麗鷗", "塔羅", "機械鍵盤", "輕小說", "女孩"],
            "hot_articles": [
                {"title": "辦公室社畜必備療癒放鬆小物", "reactions": 200, "board": "女孩"},
                {"title": "瑜珈療癒力", "reactions": 150, "board": "健身"},
            ],
            "related_searches": ["療癒小物", "療癒系", "療癒貓"],
            "metadata": {"search_date": "2026-01-25"}
        },
        {
            "keyword": "壓力大",
            "article_count": 66,
            "followers": 0,
            "related_topics": ["唸書壓力大", "期末壓力大", "工作壓力大"],
            "related_boards": ["教師", "科技業", "會計", "研究所", "軟體工程師"],
            "hot_articles": [
                {"title": "女友薪水是我的三倍...快窒息了", "reactions": 1949, "board": "感情"},
                {"title": "台灣成最不想生國家第一名", "reactions": 1086, "board": "閒聊"},
                {"title": "今年房仲收入420萬，我卻高興不起來", "reactions": 402, "board": "工作"},
                {"title": "迴避型都應該滾回自己的殼裡", "reactions": 333, "board": "感情"},
                {"title": "剛入職壓力大到哭", "reactions": 187, "board": "公職"},
                {"title": "女友家境太好，壓力大到想分手", "reactions": 177, "board": "感情"},
            ],
            "related_searches": ["工作壓力大", "上班壓力大", "壓力大皮膚"],
            "metadata": {"search_date": "2026-01-25"}
        },
        {
            "keyword": "躺平",
            "article_count": 309,
            "followers": 95,
            "related_topics": ["躺平族", "躺平主義"],
            "related_boards": ["科技業", "心情", "工作", "閒聊", "股票"],
            "hot_articles": [
                {"title": "為什麼這種房子都要破千萬？", "reactions": 768, "board": "閒聊"},
                {"title": "終於存到一百萬了！", "reactions": 677, "board": "理財"},
                {"title": "別再發那些『精緻生活』文了", "reactions": 642, "board": "心情"},
                {"title": "舒服躺平還是享受紅利", "reactions": 124, "board": "科技業"},
                {"title": "近四十歲失業，股票2500萬，能躺平嗎？", "reactions": 106, "board": "心情"},
                {"title": "哪間公司可以躺平吃大鍋飯?", "reactions": 61, "board": "科技業"},
            ],
            "related_searches": ["躺平人生", "躺平工作", "全躺平"],
            "metadata": {"search_date": "2026-01-25"}
        },
        {
            "keyword": "耍廢",
            "article_count": 203,
            "followers": 6,
            "related_topics": ["耍廢中", "在家耍廢"],
            "related_boards": ["閒聊", "心情", "旅遊", "研究所"],
            "hot_articles": [
                {"title": "研究生的寒假日記", "reactions": 961, "board": "研究所"},
                {"title": "竹科工程師的省錢秘訣", "reactions": 807, "board": "科技業"},
                {"title": "忽然發現，長大後好難好好休息", "reactions": 161, "board": "閒聊"},
                {"title": "43歲沒工作，耍廢在家", "reactions": 155, "board": "閒聊"},
                {"title": "大家一起來耍廢", "reactions": 158, "board": "梗圖"},
            ],
            "related_searches": ["在家耍廢"],
            "metadata": {"search_date": "2026-01-25"}
        },
        {
            "keyword": "放鬆",
            "article_count": 1193,
            "followers": 22,
            "related_topics": ["筋膜放鬆", "伸展放鬆"],
            "related_boards": ["健身", "跑步", "旅遊", "女孩", "心情"],
            "hot_articles": [
                {"title": "辦公室社畜必備！療癒放鬆小物！", "reactions": 200, "board": "女孩"},
                {"title": "過了30歲再也不買早去晚回", "reactions": 201, "board": "旅遊"},
                {"title": "長大真的好難放鬆自己", "reactions": 50, "board": "心情"},
                {"title": "美軍飛行員在使用的2分鐘快速入睡方法", "reactions": 100, "board": "個人牆"},
                {"title": "按摩椅推薦-在家就能放鬆的懶人救星", "reactions": 83, "board": "個人牆"},
            ],
            "related_searches": ["怎麼放鬆"],
            "metadata": {"search_date": "2026-01-25"}
        },
    ]
    
    # 儲存到 Firebase
    result = storage.save_all_research(research_results)
    
    # 額外儲存高互動文章
    all_hot_articles = []
    for research in research_results:
        keyword = research["keyword"]
        for article in research.get("hot_articles", []):
            article["keywords"] = [keyword]
            all_hot_articles.append(article)
    
    # 儲存熱門文章
    for article in all_hot_articles:
        storage.save_hot_article(article)
    
    print(f"\n🎉 儲存完成！")
    print(f"   - 關鍵字研究: {result['saved_count']} 筆")
    print(f"   - 熱門文章: {len(all_hot_articles)} 篇")
    
    return result


if __name__ == "__main__":
    save_charging_world_research()
