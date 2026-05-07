"""
RQData 扩展数据下载脚本 (修复版)

下载内容：
1. 期货扩展数据（连续合约、主力行情）
2. 股票扩展数据（大宗交易、龙虎榜、股东等）
3. 财务细分因子 + 其他因子（排除技术因子和WorldQuant因子）
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.common import setup_license
import rqdatac as rq

# 初始化
setup_license()
rq.init()

# 输出目录
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 全局股票列表（延迟加载）
_STOCK_LIST = None


def get_stock_list():
    """获取所有A股股票列表"""
    global _STOCK_LIST
    if _STOCK_LIST is None:
        stocks = rq.all_instruments('CS')
        _STOCK_LIST = stocks['order_book_id'].tolist()
    return _STOCK_LIST


def check_quota():
    """检查剩余配额"""
    try:
        info = rq.user.get_quota()
        used = info.get('used', 0)
        total = info.get('total', 1024)
        remaining = total - used
        print(f"📊 配额: 已用 {used:.1f}MB / {total:.1f}MB, 剩余 {remaining:.1f}MB")
        return remaining
    except Exception as e:
        print(f"⚠️ 无法获取配额信息: {e}")
        return 1024


# ============================================================
# 1. 期货扩展数据
# ============================================================

def download_continuous_contracts():
    """下载连续合约映射"""
    print("\n" + "=" * 60)
    print("📥 下载连续合约映射...")

    output_file = OUTPUT_DIR / "futures" / "continuous_contracts.parquet"
    if output_file.exists():
        print(f"  ⏭️ 已存在: {output_file}")
        return

    try:
        underlyings = ['IF', 'IC', 'IH', 'IM', 'T', 'TF', 'TS', 'TL', 'AG', 'AU', 'CU', 'AL', 'ZN', 'RB', 'HC']
        dfs = []

        for underlying in underlyings:
            try:
                print(f"  获取 {underlying} 连续合约...")
                df = rq.futures.get_continuous_contracts(underlying, start_date="20150101", end_date=datetime.now().strftime("%Y%m%d"))
                if df is not None and len(df) > 0:
                    df = df.reset_index()
                    dfs.append(df)
                    print(f"    ✅ {underlying}: {len(df)} 行")
            except Exception as e:
                print(f"    ❌ {underlying}: {e}")

        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            merged.to_parquet(output_file, index=False)
            print(f"✅ 连续合约保存: {output_file} ({len(merged)} 行)")

        check_quota()
    except Exception as e:
        print(f"❌ 连续合约下载失败: {e}")


def download_dominant_price():
    """下载主力合约行情"""
    print("\n" + "=" * 60)
    print("📥 下载主力合约行情...")

    output_file = OUTPUT_DIR / "futures" / "dominant_price.parquet"
    if output_file.exists():
        print(f"  ⏭️ 已存在: {output_file}")
        return

    try:
        underlyings = ['IF', 'IC', 'IH', 'IM', 'T', 'TF', 'TS', 'TL', 'AG', 'AU', 'CU', 'AL', 'ZN', 'RB', 'HC']
        dfs = []

        for underlying in underlyings:
            try:
                print(f"  获取 {underlying} 主力行情...")
                df = rq.futures.get_dominant_price(underlying, start_date="20150101", end_date=datetime.now().strftime("%Y%m%d"), fields=['open', 'high', 'low', 'close', 'volume'])
                if df is not None and len(df) > 0:
                    df = df.reset_index()
                    df['underlying'] = underlying
                    dfs.append(df)
                    print(f"    ✅ {underlying}: {len(df)} 行")
            except Exception as e:
                print(f"    ❌ {underlying}: {e}")

        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            merged.to_parquet(output_file, index=False)
            print(f"✅ 主力行情保存: {output_file} ({len(merged)} 行)")

        check_quota()
    except Exception as e:
        print(f"❌ 主力行情下载失败: {e}")


# ============================================================
# 2. 股票扩展数据
# ============================================================

def download_block_trade():
    """下载大宗交易数据"""
    print("\n" + "=" * 60)
    print("📥 下载大宗交易数据...")

    output_file = OUTPUT_DIR / "stock" / "block_trade.parquet"
    if output_file.exists():
        print(f"  ⏭️ 已存在: {output_file}")
        return

    try:
        stock_list = get_stock_list()
        print(f"  股票数量: {len(stock_list)}")

        # 分批下载
        batch_size = 200
        dfs = []

        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i+batch_size]
            print(f"  批次 {i//batch_size + 1}: {i+1}-{min(i+batch_size, len(stock_list))}")

            try:
                df = rq.get_block_trade(batch, start_date="20200101", end_date=datetime.now().strftime("%Y%m%d"))
                if df is not None and len(df) > 0:
                    df = df.reset_index()
                    dfs.append(df)
                    print(f"    ✅ {len(df)} 行")
            except Exception as e:
                print(f"    ❌ {e}")

            if check_quota() < 100:
                print("⚠️ 配额不足，停止下载")
                break

        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            merged.to_parquet(output_file, index=False)
            print(f"✅ 大宗交易保存: {output_file} ({len(merged)} 行)")

    except Exception as e:
        print(f"❌ 大宗交易下载失败: {e}")


def download_holder_number():
    """下载股东户数数据"""
    print("\n" + "=" * 60)
    print("📥 下载股东户数数据...")

    output_file = OUTPUT_DIR / "stock" / "holder_number.parquet"
    if output_file.exists():
        print(f"  ⏭️ 已存在: {output_file}")
        return

    try:
        stock_list = get_stock_list()
        print(f"  股票数量: {len(stock_list)}")

        batch_size = 500
        dfs = []

        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i+batch_size]
            print(f"  批次 {i//batch_size + 1}: {i+1}-{min(i+batch_size, len(stock_list))}")

            try:
                df = rq.get_holder_number(batch, start_date="20150101", end_date=datetime.now().strftime("%Y%m%d"))
                if df is not None and len(df) > 0:
                    df = df.reset_index()
                    dfs.append(df)
                    print(f"    ✅ {len(df)} 行")
            except Exception as e:
                print(f"    ❌ {e}")

        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            merged.to_parquet(output_file, index=False)
            print(f"✅ 股东户数保存: {output_file} ({len(merged)} 行)")

        check_quota()
    except Exception as e:
        print(f"❌ 股东户数下载失败: {e}")


def download_leader_shares_change():
    """下载龙虎榜数据"""
    print("\n" + "=" * 60)
    print("📥 下载龙虎榜数据...")

    output_file = OUTPUT_DIR / "stock" / "leader_shares_change.parquet"
    if output_file.exists():
        print(f"  ⏭️ 已存在: {output_file}")
        return

    try:
        stock_list = get_stock_list()
        print(f"  股票数量: {len(stock_list)}")

        batch_size = 200
        dfs = []

        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i+batch_size]
            print(f"  批次 {i//batch_size + 1}: {i+1}-{min(i+batch_size, len(stock_list))}")

            try:
                df = rq.get_leader_shares_change(batch, start_date="20200101", end_date=datetime.now().strftime("%Y%m%d"))
                if df is not None and len(df) > 0:
                    df = df.reset_index()
                    dfs.append(df)
                    print(f"    ✅ {len(df)} 行")
            except Exception as e:
                print(f"    ❌ {e}")

            if check_quota() < 100:
                print("⚠️ 配额不足，停止下载")
                break

        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            merged.to_parquet(output_file, index=False)
            print(f"✅ 龙虎榜保存: {output_file} ({len(merged)} 行)")

    except Exception as e:
        print(f"❌ 龙虎榜下载失败: {e}")


def download_private_placement():
    """下载定向增发数据"""
    print("\n" + "=" * 60)
    print("📥 下载定向增发数据...")

    output_file = OUTPUT_DIR / "stock" / "private_placement.parquet"
    if output_file.exists():
        print(f"  ⏭️ 已存在: {output_file}")
        return

    try:
        stock_list = get_stock_list()
        print(f"  股票数量: {len(stock_list)}")

        batch_size = 200
        dfs = []

        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i+batch_size]
            print(f"  批次 {i//batch_size + 1}: {i+1}-{min(i+batch_size, len(stock_list))}")

            try:
                df = rq.get_private_placement(batch, start_date="20150101", end_date=datetime.now().strftime("%Y%m%d"))
                if df is not None and len(df) > 0:
                    dfs.append(df)
                    print(f"    ✅ {len(df)} 行")
            except Exception as e:
                print(f"    ❌ {e}")

        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            merged.to_parquet(output_file, index=False)
            print(f"✅ 定向增发保存: {output_file} ({len(merged)} 行)")

        check_quota()
    except Exception as e:
        print(f"❌ 定向增发下载失败: {e}")


def download_restricted_shares():
    """下载限售股解禁数据"""
    print("\n" + "=" * 60)
    print("📥 下载限售股解禁数据...")

    output_file = OUTPUT_DIR / "stock" / "restricted_shares.parquet"
    if output_file.exists():
        print(f"  ⏭️ 已存在: {output_file}")
        return

    try:
        stock_list = get_stock_list()
        print(f"  股票数量: {len(stock_list)}")

        batch_size = 200
        dfs = []

        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i+batch_size]
            print(f"  批次 {i//batch_size + 1}: {i+1}-{min(i+batch_size, len(stock_list))}")

            try:
                df = rq.get_restricted_shares(batch, start_date="20150101", end_date="20261231")
                if df is not None and len(df) > 0:
                    dfs.append(df)
                    print(f"    ✅ {len(df)} 行")
            except Exception as e:
                print(f"    ❌ {e}")

        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            merged.to_parquet(output_file, index=False)
            print(f"✅ 限售股解禁保存: {output_file} ({len(merged)} 行)")

        check_quota()
    except Exception as e:
        print(f"❌ 限售股解禁下载失败: {e}")


def download_stock_connect_holding_details():
    """下载沪深通持股明细"""
    print("\n" + "=" * 60)
    print("📥 下载沪深通持股明细...")

    output_file = OUTPUT_DIR / "stock" / "stock_connect_holding_details.parquet"
    if output_file.exists():
        print(f"  ⏭️ 已存在: {output_file}")
        return

    try:
        stock_list = get_stock_list()
        print(f"  股票数量: {len(stock_list)}")

        batch_size = 100
        dfs = []

        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i+batch_size]
            print(f"  批次 {i//batch_size + 1}: {i+1}-{min(i+batch_size, len(stock_list))}")

            try:
                df = rq.get_stock_connect_holding_details(batch, start_date="20200101", end_date=datetime.now().strftime("%Y%m%d"))
                if df is not None and len(df) > 0:
                    df = df.reset_index()
                    dfs.append(df)
                    print(f"    ✅ {len(df)} 行")
            except Exception as e:
                print(f"    ❌ {e}")

            if check_quota() < 100:
                print("⚠️ 配额不足，停止下载")
                break

        if dfs:
            merged = pd.concat(dfs, ignore_index=True)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            merged.to_parquet(output_file, index=False)
            print(f"✅ 沪深通持股明细保存: {output_file} ({len(merged)} 行)")

    except Exception as e:
        print(f"❌ 沪深通持股明细下载失败: {e}")


def download_abnormal_stocks():
    """下载异常股票数据"""
    print("\n" + "=" * 60)
    print("📥 下载异常股票数据...")

    output_file = OUTPUT_DIR / "stock" / "abnormal_stocks.parquet"
    if output_file.exists():
        print(f"  ⏭️ 已存在: {output_file}")
        return

    try:
        df = rq.get_abnormal_stocks(start_date="20200101", end_date=datetime.now().strftime("%Y%m%d"))
        if df is not None and len(df) > 0:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(output_file, index=False)
            print(f"✅ 异常股票保存: {output_file} ({len(df)} 行)")
        else:
            print("⚠️ 异常股票数据为空")

        check_quota()
    except Exception as e:
        print(f"❌ 异常股票下载失败: {e}")


# ============================================================
# 3. 因子数据下载
# ============================================================

def get_factor_lists():
    """获取需要下载的因子列表（排除技术因子和WorldQuant因子）"""

    all_factors = rq.get_all_factor_names()

    # 已下载的因子
    import os
    factor_dir = OUTPUT_DIR / "factor"
    downloaded = [f.replace('.parquet', '') for f in os.listdir(factor_dir) if f.endswith('.parquet')] if factor_dir.exists() else []

    # 技术因子模式（排除）
    tech_patterns = ['BIAS', 'BR', 'CR', 'CYF', 'CYR', 'DAVOL', 'DI', 'DKX', 'DPO',
                     'EMA', 'HMA', 'LMA', 'VMA', 'WMA', 'MA3', 'MA30', 'MA55',
                     'MABIAS', 'MACR', 'MACYR', 'MADKX', 'MADPO', 'MAMASS', 'MAMTM',
                     'MARSI', 'MATAPI', 'MATRIX', 'MAUDL', 'MAVR', 'MCST', 'MDD',
                     'MFI', 'MTM', 'OBOS', 'OBV', 'OSC', 'PCNT', 'QTYR', 'ROC',
                     'SKD', 'SWL', 'SWS', 'SY', 'TAPI', 'TR', 'TRIX', 'UDL', 'VOL',
                     'VOLT', 'VR', 'WR', 'LWR', 'ACCER', 'ADTM', 'ADX', 'ADXR',
                     'AMP', 'AMV', 'AR', 'AROON', 'ASI', 'ATR', 'BBI', 'BBIBOLL',
                     'CCI', 'KDJ', 'MACD', 'RSI', 'BOLL', 'MA', 'WorldQuant']

    not_downloaded = []
    for f in all_factors:
        if f in downloaded:
            continue
        if any(x in f for x in ['_lyr_', '_mrq_', '_ttm_']):
            continue
        # 检查是否是技术因子
        is_tech = False
        for pattern in tech_patterns:
            if f.startswith(pattern) or f == pattern:
                is_tech = True
                break
        if is_tech:
            continue
        not_downloaded.append(f)

    return not_downloaded


def download_factors_batch(factors: list, batch_size: int = 20):
    """批量下载因子数据"""
    print("\n" + "=" * 60)
    print(f"📥 开始下载 {len(factors)} 个因子...")

    stock_list = get_stock_list()
    print(f"  股票数量: {len(stock_list)}")

    total = len(factors)
    downloaded = 0
    failed = []
    total_rows = 0

    output_dir = OUTPUT_DIR / "factor"
    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(0, total, batch_size):
        batch = factors[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        print(f"\n批次 {batch_num}/{total_batches}: {i+1}-{min(i+batch_size, total)}")
        print(f"  因子: {batch[:5]}...")

        try:
            df = rq.get_factor(
                order_book_ids=stock_list,
                factor=batch,
                start_date="20200101",
                end_date=datetime.now().strftime("%Y%m%d")
            )

            if df is not None and len(df) > 0:
                # 保存每个因子单独的文件
                df = df.reset_index()
                for factor in batch:
                    if factor in df.columns:
                        factor_df = df[['date', 'order_book_id', factor]].dropna()
                        if len(factor_df) > 0:
                            output_file = output_dir / f"{factor}.parquet"
                            factor_df.to_parquet(output_file, index=False)
                            downloaded += 1
                            total_rows += len(factor_df)
                print(f"  ✅ 成功，已保存 {len([f for f in batch if f in df.columns])} 个因子")
            else:
                print(f"  ⚠️ 空数据")
                failed.extend(batch)

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            failed.extend(batch)

        # 检查配额
        if check_quota() < 100:
            print("\n⚠️ 配额不足，停止下载")
            break

    print("\n" + "=" * 60)
    print(f"因子下载完成: {downloaded}/{total}, 共 {total_rows} 行数据")
    if failed:
        print(f"失败因子数: {len(failed)}")
        with open("data/failed_factors.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(failed))

    return downloaded, failed


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("🚀 RQData 扩展数据下载 (修复版)")
    print("=" * 60)

    # 检查配额
    remaining = check_quota()
    if remaining < 100:
        print("⚠️ 配额不足，请稍后再试")
        return

    # 1. 期货扩展数据
    print("\n" + "=" * 60)
    print("📌 第一部分: 期货扩展数据")
    print("=" * 60)

    download_continuous_contracts()
    download_dominant_price()

    # 2. 股票扩展数据
    print("\n" + "=" * 60)
    print("📌 第二部分: 股票扩展数据")
    print("=" * 60)

    download_block_trade()
    download_holder_number()
    download_leader_shares_change()
    download_private_placement()
    download_restricted_shares()
    download_stock_connect_holding_details()
    download_abnormal_stocks()

    # 3. 因子数据
    print("\n" + "=" * 60)
    print("📌 第三部分: 因子数据（财务细分+其他因子）")
    print("=" * 60)

    factors = get_factor_lists()
    print(f"待下载因子数: {len(factors)}")

    if factors:
        download_factors_batch(factors, batch_size=20)

    # 最终检查
    print("\n" + "=" * 60)
    print("📊 下载完成，最终配额状态:")
    print("=" * 60)
    check_quota()


if __name__ == "__main__":
    main()
