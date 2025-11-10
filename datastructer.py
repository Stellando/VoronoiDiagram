# 資料結構部分
import math
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class PointType(Enum):
    """點的類型"""
    SITE = "site"  # 原始輸入點（站點）
    VORONOI_VERTEX = "voronoi_vertex"  # Voronoi 頂點（中垂線交點）


@dataclass
class Point:
    """
    座標點基礎類別
    用於表示平面上的點
    """
    x: float
    y: float
    point_type: PointType = PointType.SITE
    id: Optional[int] = None  # 用於追蹤和識別
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return math.isclose(self.x, other.x, abs_tol=1e-9) and \
               math.isclose(self.y, other.y, abs_tol=1e-9)
    
    def __repr__(self):
        return f"Point({self.x:.2f}, {self.y:.2f}, {self.point_type.value})"
    
    def distance_to(self, other: 'Point') -> float:
        """計算到另一點的距離"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def to_tuple(self) -> Tuple[float, float]:
        """轉換為座標tuple"""
        return (self.x, self.y)


@dataclass
class VoronoiSite(Point):
    """
    Voronoi Site（輸入的原始點）
    這些是需要進行 Voronoi 分割的點
    """
    edges: List['VoronoiEdge'] = field(default_factory=list)  # 此點產生的所有中垂線
    cell: Optional['VoronoiCell'] = None  # 此點的 Voronoi cell
    
    def __post_init__(self):
        self.point_type = PointType.SITE
        if not self.edges:
            self.edges = []
    
    def __hash__(self):
        # 使用座標和 id 來雜湊，忽略可變字段
        return hash((self.x, self.y, self.id))
    
    def __eq__(self, other):
        if not isinstance(other, VoronoiSite):
            return False
        # 如果有 id，比較 id；否則比較座標
        if self.id is not None and other.id is not None:
            return self.id == other.id
        return math.isclose(self.x, other.x, abs_tol=1e-9) and \
               math.isclose(self.y, other.y, abs_tol=1e-9)
    
    def add_edge(self, edge: 'VoronoiEdge'):
        """添加與此站點相關的邊"""
        if edge not in self.edges:
            self.edges.append(edge)
    
    def remove_edge(self, edge: 'VoronoiEdge'):
        """移除與此站點相關的邊"""
        if edge in self.edges:
            self.edges.remove(edge)


@dataclass
class VoronoiVertex(Point):
    """
    Voronoi Vertex（中垂線的交點）
    
    類型：
    1. 外心（Circumcenter）：三個站點的中垂線交點，在處理三角形時創建
    2. 交匯點（Junction）：Hyperplane 截斷產生的交點，連接被截斷的邊和前後兩段 hyperplane
    """
    incident_edges: List['VoronoiEdge'] = field(default_factory=list)  # 相交於此點的邊
    sites: List[VoronoiSite] = field(default_factory=list)  # 形成此頂點的站點
    is_junction: bool = False  # 是否為交匯點（Hyperplane 碰撞產生）
    
    def __post_init__(self):
        self.point_type = PointType.VORONOI_VERTEX
        if not self.incident_edges:
            self.incident_edges = []
        if not self.sites:
            self.sites = []
    
    def degree(self) -> int:
        """返回此頂點的度數（相交的邊數）"""
        return len(self.incident_edges)
    
    def is_circumcenter(self) -> bool:
        """判斷是否為外心（三個站點形成）"""
        return len(self.sites) == 3 and not self.is_junction
    
    def is_orphanable(self) -> bool:
        """判斷是否可能成為孤立點（外心或交匯點，初始度數為 3）"""
        return self.is_circumcenter() or self.is_junction


@dataclass
class VoronoiEdge:
    """
    Voronoi Edge（中垂線）
    兩個站點之間的垂直平分線（或其一部分）
    """
    site1: VoronoiSite  # 產生此邊的第一個站點
    site2: VoronoiSite  # 產生此邊的第二個站點
    _start: Optional[VoronoiVertex] = field(default=None, init=False, repr=False)  # 內部起始頂點
    _end: Optional[VoronoiVertex] = field(default=None, init=False, repr=False)  # 內部結束頂點
    is_hyperplane: bool = False  # 是否為 divide-conquer 過程中的分割線
    is_infinite: bool = False  # 是否為無限延伸的邊
    id: Optional[int] = None
    
    # 中垂線的數學參數
    slope: Optional[float] = None  # 斜率（垂直線為 None）
    intercept: Optional[float] = None  # y 截距
    is_vertical: bool = False  # 是否為垂直線
    vertical_x: Optional[float] = None  # 垂直線的 x 座標
    
    # 法向量線（Normal Line）參數：通過 site1 和 site2 的直線
    # 方程式: normal_a * x + normal_b * y + normal_c = 0
    normal_a: Optional[float] = None
    normal_b: Optional[float] = None
    normal_c: Optional[float] = None
    
    def __post_init__(self):
        """初始化時計算中垂線參數和法向量線參數"""
        self._calculate_perpendicular_bisector()
        self._calculate_normal_line()
    
    @property
    def start(self) -> Optional[VoronoiVertex]:
        """獲取起始頂點"""
        return self._start
    
    @start.setter
    def start(self, vertex: Optional[VoronoiVertex]):
        """
        設定起始頂點，自動維護頂點的 incident_edges 列表
        """
        # 從舊頂點移除此邊
        if self._start and self in self._start.incident_edges:
            self._start.incident_edges.remove(self)
        
        # 設定新頂點
        self._start = vertex
        
        # 加入新頂點的 incident_edges
        if vertex and self not in vertex.incident_edges:
            vertex.incident_edges.append(self)
    
    @property
    def end(self) -> Optional[VoronoiVertex]:
        """獲取結束頂點"""
        return self._end
    
    @end.setter
    def end(self, vertex: Optional[VoronoiVertex]):
        """
        設定結束頂點，自動維護頂點的 incident_edges 列表
        """
        # 從舊頂點移除此邊
        if self._end and self in self._end.incident_edges:
            self._end.incident_edges.remove(self)
        
        # 設定新頂點
        self._end = vertex
        
        # 加入新頂點的 incident_edges
        if vertex and self not in vertex.incident_edges:
            vertex.incident_edges.append(self)
    
    def _calculate_perpendicular_bisector(self):
        """計算兩點的垂直平分線參數"""
        # 計算中點
        mid_x = (self.site1.x + self.site2.x) / 2
        mid_y = (self.site1.y + self.site2.y) / 2
        
        # 計算原始線段的斜率
        dx = self.site2.x - self.site1.x
        dy = self.site2.y - self.site1.y
        
        # 處理垂直情況
        if abs(dx) < 1e-9:  # 原始線段垂直，中垂線水平
            self.is_vertical = False
            self.slope = 0
            self.intercept = mid_y
            self.vertical_x = None
        elif abs(dy) < 1e-9:  # 原始線段水平，中垂線垂直
            self.is_vertical = True
            self.vertical_x = mid_x
            self.slope = None
            self.intercept = None
        else:
            # 一般情況：中垂線斜率 = -1 / 原始斜率
            original_slope = dy / dx
            self.slope = -1 / original_slope
            self.is_vertical = False
            # y - mid_y = slope * (x - mid_x)
            # y = slope * x - slope * mid_x + mid_y
            self.intercept = mid_y - self.slope * mid_x
            self.vertical_x = None
    
    def _calculate_normal_line(self):
        """
        計算法向量線（通過 site1 和 site2 的直線）
        方程式: ax + by + c = 0
        用途：判斷點在中垂線的哪一側
        """
        # 法向量線就是通過 site1 和 site2 的直線
        # 使用兩點式: (y - y1) / (y2 - y1) = (x - x1) / (x2 - x1)
        # 整理成一般式: a*x + b*y + c = 0
        
        x1, y1 = self.site1.x, self.site1.y
        x2, y2 = self.site2.x, self.site2.y
        
        # 向量 (x2-x1, y2-y1) 的法向量是 (y2-y1, -(x2-x1))
        # 但我們要的是通過兩點的直線，所以用標準公式：
        # (y2-y1)*x - (x2-x1)*y + (x2-x1)*y1 - (y2-y1)*x1 = 0
        
        self.normal_a = y2 - y1
        self.normal_b = -(x2 - x1)
        self.normal_c = (x2 - x1) * y1 - (y2 - y1) * x1
    
    def get_normal_line_value(self, x: float, y: float) -> float:
        """
        計算點 (x, y) 代入法向量線方程式的值
        返回: a*x + b*y + c
        
        用途：判斷點在法向量線的哪一側
        - 返回值 > 0: 點在法向量線的一側
        - 返回值 < 0: 點在法向量線的另一側
        - 返回值 = 0: 點在法向量線上
        """
        if self.normal_a is None or self.normal_b is None or self.normal_c is None:
            raise ValueError("法向量線參數未初始化")
        
        return self.normal_a * x + self.normal_b * y + self.normal_c
    
    def get_midpoint(self) -> Tuple[float, float]:
        """獲取兩站點的中點"""
        return ((self.site1.x + self.site2.x) / 2, 
                (self.site1.y + self.site2.y) / 2)
    
    def point_on_line(self, t: float) -> Tuple[float, float]:
        """
        獲取線上的點，參數化表示
        t: 參數（0 表示中點，正負表示方向）
        """
        mid_x, mid_y = self.get_midpoint()
        
        if self.is_vertical:
            return (self.vertical_x, mid_y + t)
        else:
            # 沿著中垂線的方向向量
            # 方向向量垂直於兩站點連線
            dx = self.site2.x - self.site1.x
            dy = self.site2.y - self.site1.y
            length = math.sqrt(dx*dx + dy*dy)
            
            # 單位法向量（垂直方向）
            nx = -dy / length
            ny = dx / length
            
            return (mid_x + t * nx, mid_y + t * ny)
    
    def intersect_with(self, other: 'VoronoiEdge') -> Optional[Tuple[float, float]]:
        """
        計算與另一條邊的交點
        返回交點座標，如果平行則返回 None
        """
        # 兩條都是垂直線
        if self.is_vertical and other.is_vertical:
            return None  # 平行或重合
        
        # 只有 self 是垂直線
        if self.is_vertical:
            x = self.vertical_x
            y = other.slope * x + other.intercept
            return (x, y)
        
        # 只有 other 是垂直線
        if other.is_vertical:
            x = other.vertical_x
            y = self.slope * x + self.intercept
            return (x, y)
        
        # 都不是垂直線
        # y = slope1 * x + intercept1
        # y = slope2 * x + intercept2
        if abs(self.slope - other.slope) < 1e-9:
            return None  # 平行
        
        x = (other.intercept - self.intercept) / (self.slope - other.slope)
        y = self.slope * x + self.intercept
        return (x, y)
    
    def copy_snapshot(self) -> 'VoronoiEdge':
        """
        創建當前邊的快照（用於 step-by-step 顯示）
        複製邊的當前狀態，包括端點位置
        """
        from copy import copy
        # 創建一個新的 VoronoiEdge，但共享 site1 和 site2
        snapshot = VoronoiEdge(
            site1=self.site1,
            site2=self.site2,
            is_hyperplane=self.is_hyperplane,
            is_infinite=self.is_infinite,
            id=self.id
        )
        # 直接設置私有變數，避免觸發 property setter（快照不需要維護 incident_edges）
        snapshot._start = copy(self.start) if self.start else None
        snapshot._end = copy(self.end) if self.end else None
        
        # 複製數學參數（這些在 __post_init__ 會重新計算，但我們要保留當前值）
        snapshot.slope = self.slope
        snapshot.intercept = self.intercept
        snapshot.is_vertical = self.is_vertical
        snapshot.vertical_x = self.vertical_x
        snapshot.normal_a = self.normal_a
        snapshot.normal_b = self.normal_b
        snapshot.normal_c = self.normal_c
        return snapshot
    
    def __repr__(self):
        hp = " [HP]" if self.is_hyperplane else ""
        inf = " [INF]" if self.is_infinite else ""
        return f"Edge({self.site1.id}-{self.site2.id}{hp}{inf})"
    
    def __hash__(self):
        return hash((id(self.site1), id(self.site2)))


@dataclass
class VoronoiCell:
    """
    Voronoi Cell（Voronoi 區域）
    代表某個站點的勢力範圍
    """
    site: VoronoiSite  # 此 cell 對應的站點
    vertices: List[VoronoiVertex] = field(default_factory=list)  # 構成此 cell 的頂點（按順序）
    edges: List[VoronoiEdge] = field(default_factory=list)  # 構成此 cell 的邊


@dataclass
class ConvexHull:
    """
    凸包資料結構
    用於 divide-conquer 過程中的合併操作
    """
    points: List[Point] = field(default_factory=list)  # 凸包上的點（按逆時針順序）
    edges: List[Tuple[Point, Point]] = field(default_factory=list)  # 凸包的邊
    
    def add_point(self, point: Point):
        """添加點到凸包"""
        if point not in self.points:
            self.points.append(point)
    
    def compute_edges(self):
        """計算凸包的邊"""
        self.edges = []
        n = len(self.points)
        for i in range(n):
            self.edges.append((self.points[i], self.points[(i+1) % n]))
    
    def contains_point(self, point: Point) -> bool:
        """檢查點是否在凸包內或邊上"""
        if point in self.points:
            return True
        # TODO: 實作點在多邊形內的判斷
        return False


@dataclass
class MergeStep:
    """
    記錄一次 merge 操作的狀態
    用於 step-by-step 顯示
    """
    step_id: int  # 步驟編號
    description: str  # 步驟描述
    
    # 當前狀態快照
    left_sites: List[VoronoiSite] = field(default_factory=list)  # 左半邊的站點
    right_sites: List[VoronoiSite] = field(default_factory=list)  # 右半邊的站點
    left_edges: List[VoronoiEdge] = field(default_factory=list)  # 左半邊的邊
    right_edges: List[VoronoiEdge] = field(default_factory=list)  # 右半邊的邊
    
    hyperplane: Optional[VoronoiEdge] = None  # 當前的分割線
    left_hull: Optional[ConvexHull] = None  # 左半邊凸包
    right_hull: Optional[ConvexHull] = None  # 右半邊凸包
    merged_hull: Optional[ConvexHull] = None  # 合併後的凸包
    
    # 當前處理的關鍵點
    current_edge: Optional[VoronoiEdge] = None  # 正在處理的邊
    intersection_point: Optional[VoronoiVertex] = None  # 交點
    
    # 標記被修改/刪除的元素
    modified_edges: Set[VoronoiEdge] = field(default_factory=set)
    deleted_edges: Set[VoronoiEdge] = field(default_factory=set)
    new_edges: Set[VoronoiEdge] = field(default_factory=set)


class VoronoiDiagram:
    """
    Voronoi Diagram 主類別
    管理整個 Voronoi 圖的結構
    """
    
    def __init__(self):
        self.sites: List[VoronoiSite] = []  # 所有站點
        self.vertices: List[VoronoiVertex] = []  # 所有 Voronoi 頂點
        self.edges: List[VoronoiEdge] = []  # 所有邊
        self.cells: List[VoronoiCell] = []  # 所有 cell
        self.convex_hull: Optional[ConvexHull] = None  # 整體凸包
        
        # Step-by-step 記錄
        self.merge_steps: List[MergeStep] = []
        self.current_step: int = -1  # -1 表示顯示完整結果
        
        # ID 計數器
        self._site_id_counter: int = 0
        self._edge_id_counter: int = 0
        self._vertex_id_counter: int = 0
    
    def add_site(self, x: float, y: float) -> VoronoiSite:
        """添加一個新的站點"""
        site = VoronoiSite(x=x, y=y, id=self._site_id_counter)
        self._site_id_counter += 1
        self.sites.append(site)
        return site
    
    def add_sites_from_list(self, points: List[Tuple[float, float]]):
        """從座標列表批量添加站點"""
        for x, y in points:
            self.add_site(x, y)
    
    def create_edge(self, site1: VoronoiSite, site2: VoronoiSite, 
                    is_hyperplane: bool = False) -> VoronoiEdge:
        """創建一條新的 Voronoi 邊"""
        edge = VoronoiEdge(
            site1=site1,
            site2=site2,
            is_hyperplane=is_hyperplane,
            id=self._edge_id_counter
        )
        self._edge_id_counter += 1
        self.edges.append(edge)
        
        # 關聯到站點
        site1.add_edge(edge)
        site2.add_edge(edge)
        
        return edge
    
    def create_vertex(self, x: float, y: float, 
                     sites: Optional[List[VoronoiSite]] = None) -> VoronoiVertex:
        """創建一個新的 Voronoi 頂點"""
        vertex = VoronoiVertex(
            x=x,
            y=y,
            id=self._vertex_id_counter,
            sites=sites if sites else []
        )
        self._vertex_id_counter += 1
        self.vertices.append(vertex)
        return vertex
    
    def remove_edge(self, edge: VoronoiEdge):
        """移除一條邊"""
        if edge in self.edges:
            self.edges.remove(edge)
            edge.site1.remove_edge(edge)
            edge.site2.remove_edge(edge)
            
            # 從頂點的 incident_edges 中移除
            if edge.start and edge in edge.start.incident_edges:
                edge.start.incident_edges.remove(edge)
            if edge.end and edge in edge.end.incident_edges:
                edge.end.incident_edges.remove(edge)
    
    def remove_orphaned_edges(self, affected_vertices: Optional[List[VoronoiVertex]] = None) -> List[VoronoiEdge]:
        """
        移除孤立的邊（連接到度數為 1 的頂點的邊）
        
        當 hyperplane 截斷導致頂點只剩一條邊連接時，該邊應該被移除。
        檢查條件：
        1. 外心頂點（Circumcenter）：len(vertex.sites) == 3 且 not is_junction
        2. 交匯點（Junction Vertex）：is_junction == True
        
        Args:
            affected_vertices: 受影響的頂點列表。如果為 None，檢查所有頂點
            
        Returns:
            被移除的邊列表
        """
        removed_edges = []
        
        # 使用列表追蹤待檢查的頂點，並手動檢查重複（因為 VoronoiVertex 無法 hash）
        if affected_vertices:
            vertices_to_check = list(affected_vertices)
        else:
            vertices_to_check = list(self.vertices)
        
        # 使用已檢查列表避免重複檢查
        checked_vertices = []
        
        print(f"  [清理] 開始檢查 {len(vertices_to_check)} 個頂點...")
        
        # 持續檢查直到沒有度數為 1 的頂點
        while vertices_to_check:
            # 取出一個頂點檢查
            vertex = vertices_to_check.pop(0)
            
            # 跳過已檢查的頂點
            if vertex in checked_vertices:
                continue
            checked_vertices.append(vertex)
            
            # **關鍵：只檢查外心或交匯點（初始度數為 3 的頂點）**
            if not vertex.is_orphanable():
                continue
            
            # 檢查這個頂點是否度數為 1
            if vertex.degree() == 1:
                # 取得唯一連接到這個頂點的邊
                orphaned_edge = vertex.incident_edges[0]
                
                vertex_type = "交匯點" if vertex.is_junction else "外心"
                print(f"  [清理] {vertex_type} (sites={len(vertex.sites)}, degree=1) at ({vertex.x:.1f}, {vertex.y:.1f})")
                print(f"  [清理] 準備移除孤立邊 #{orphaned_edge.id}: site {orphaned_edge.site1.id}-{orphaned_edge.site2.id}")
                
                # 找出這條邊的另一個端點（不是當前檢查的頂點）
                other_vertex = None
                if orphaned_edge.start == vertex:
                    other_vertex = orphaned_edge.end
                elif orphaned_edge.end == vertex:
                    other_vertex = orphaned_edge.start
                
                # 移除這條邊（會自動從 vd.edges、站點、以及兩端頂點的 incident_edges 中移除）
                self.remove_edge(orphaned_edge)
                removed_edges.append(orphaned_edge)
                
                print(f"  [清理] 已移除邊 #{orphaned_edge.id}")
                
                # 檢查另一個端點：只有當它也可能成為孤立點時才加入待檢查列表
                if other_vertex and other_vertex != vertex:
                    other_type = "交匯點" if other_vertex.is_junction else ("外心" if other_vertex.is_circumcenter() else "其他")
                    print(f"  [清理] 檢查另一個端點: {other_type}, sites={len(other_vertex.sites)}, degree={other_vertex.degree()}")
                    
                    # 只有外心或交匯點才繼續檢查
                    if other_vertex.is_orphanable() and other_vertex.degree() >= 1:
                        if other_vertex not in vertices_to_check and other_vertex not in checked_vertices:
                            print(f"  [清理] 將另一個{other_type}加入檢查列表")
                            vertices_to_check.append(other_vertex)
        
        if removed_edges:
            print(f"  [清理] 總共移除了 {len(removed_edges)} 條孤立邊")
        else:
            print(f"  [清理] 沒有找到需要移除的孤立邊")
        
        return removed_edges
    
    def clear(self):
        """清空所有資料"""
        self.sites.clear()
        self.vertices.clear()
        self.edges.clear()
        self.cells.clear()
        self.merge_steps.clear()
        self.convex_hull = None
        self.current_step = -1
        self._site_id_counter = 0
        self._edge_id_counter = 0
        self._vertex_id_counter = 0
    
    def get_step(self, step_index: int) -> Optional[MergeStep]:
        """獲取特定步驟的狀態"""
        if 0 <= step_index < len(self.merge_steps):
            return self.merge_steps[step_index]
        return None
    
    def add_merge_step(self, step: MergeStep):
        """記錄一個 merge 步驟"""
        self.merge_steps.append(step)
    
    def __repr__(self):
        return f"VoronoiDiagram(sites={len(self.sites)}, edges={len(self.edges)}, vertices={len(self.vertices)})"

