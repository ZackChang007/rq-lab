#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
下载所有期货合约列表（Parquet格式）

使用 rqdatac.futures.get_contracts() API 获取所有期货合约信息。
输出: data/futures/contracts.parquet
"""

import sys
from pathlib import Path

# 初始化许可证
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.common import setup_license

import pandas as pd
import rqdatac

setup_license()
rqdatac.init()


def download_futures_contracts():
    """下载所有期货合约列表"""
    # 期货品种列表
    types = [
        # 金融期货
        "IF", "IH", "IC", "IM",  # 股指期货
        "TF", "T", "TS", "TL",  # 国债期货
        # 商品期货
        "CU", "AL", "ZN", "AU", "AG", "RB", "HC",  # 有色/黑色
        "I", "J", "MA", "TA", "CF", "SR", "OI",  # 其他商品
        "C", "L", "M", "P", "Y", "PP"  # 农产品/化工
    ]

    all_contracts = []

    print(f"开始下载期货合约列表，共 {len(types)} 个品种...")

    for type_code in types:
        try:
            contracts = rqdatac.futures.get_contracts(type_code)
            if contracts:
                # get_contracts() returns a list of contract symbols
                if isinstance(contracts, list):
                    print(f"  {type_code}: {len(contracts)} 个合约")
                    # Convert list to DataFrame
                    df = pd.DataFrame({"contract": contracts})
                    df["type"] = type_code
                    all_contracts.append(df)
                elif isinstance(contracts, pd.DataFrame):
                    if not contracts.empty:
                        print(f"  {type_code}: {len(contracts)} 个合约")
                        contracts["type"] = type_code
                        all_contracts.append(contracts)
                    else:
                        print(f"  {type_code}: 无合约数据")
                elif isinstance(contracts, pd.Series):
                    df = contracts.to_frame(name="contract")
                    df["type"] = type_code
                    print(f"  {type_code}: {len(df)} 个合约")
                    all_contracts.append(df)
                else:
                    print(f"  {type_code}: 数据类型未知 ({type(contracts)})")
            else:
                print(f"  {type_code}: 无合约数据")
        except Exception as e:
            print(f"  {type_code}: 获取失败 - {e}")

    # 合并并保存为 Parquet
    if not all_contracts:
        print("未获取到任何合约数据")
        return {
            "success": False,
            "data_type": "contracts_parquet",
            "rows": 0,
            "error": "未获取到任何合约数据"
        }

    merged = pd.concat(all_contracts)
    total_rows = len(merged)

    output_path = Path(__file__).parent.parent.parent / "data" / "futures" / "contracts.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    merged.to_parquet(str(output_path), engine="pyarrow", compression="snappy", index=True)

    print(f"\n合约列表已保存到: {output_path}")
    print(f"总合约数: {total_rows}")

    return {
        "success": True,
        "data_type": "contracts_parquet",
        "rows": total_rows,
        "error": None
    }


if __name__ == "__main__":
    result = download_futures_contracts()
    print(f"\n结果: {result}")