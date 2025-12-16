import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable
import time
import random

allUniv = []

def getHTMLText(url, max_retries=3):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(1, 3))
            
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            r.encoding = 'utf-8'
            return r.text
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"获取页面失败: {url}")
                print(f"错误信息: {e}")
                return ""
            print(f"第{attempt+1}次尝试失败，正在重试...")
            time.sleep(2) 

def fillUnivList(soup):
    data = soup.find_all('tr')
    for tr in data:
        singleUniv = []
        ltd = tr.find_all('td')
        
        if len(ltd) < 5: 
            continue
            
        try:
            rank = ltd[0].string.strip("\n ") if ltd[0].string else ""
            singleUniv.append(rank)
            
            if len(ltd) > 1 and ltd[1].find('a'):
                name_elem = ltd[1].find('a')
                if name_elem and name_elem.string:
                    singleUniv.append(name_elem.string.strip("\n "))
                else:
                    texts = list(ltd[1].stripped_strings)
                    singleUniv.append(texts[1] if len(texts) > 1 else texts[0] if texts else "")
            else:
                singleUniv.append("")
            
            if len(ltd) > 2:
                province_text = list(ltd[2].stripped_strings)
                singleUniv.append(province_text[0] if province_text else "")
            else:
                singleUniv.append("")
            
            if len(ltd) > 3:
                type_text = list(ltd[3].stripped_strings)
                singleUniv.append(type_text[0] if type_text else "")
            else:
                singleUniv.append("")

            if len(ltd) > 4 and ltd[4].string:
                singleUniv.append(ltd[4].string.strip("\n "))
            else:
                singleUniv.append("")

            if singleUniv[0] and singleUniv[1]:  
                allUniv.append(singleUniv)
                
        except Exception as e:
            print(f"解析行数据时出错: {e}")
            continue

def getTotalPages(soup):
    try:
        pagination = soup.find('ul', {'class': 'pagination'})
        if pagination:
            page_links = pagination.find_all('li')
            if page_links:
                last_page_link = page_links[-2].find('a')
                if last_page_link and last_page_link.string:
                    return int(last_page_link.string)
        
        total_schools_elem = soup.find('div', {'class': 'page-info'})
        if total_schools_elem:
            import re
            text = total_schools_elem.get_text()
            match = re.search(r'共\s*(\d+)\s*所', text)
            if match:
                total_schools = int(match.group(1))
                return (total_schools // 30) + 1
        
        return 10
        
    except Exception as e:
        print(f"获取总页数时出错: {e}")
        return 10 

def crawlAllPages(base_url, year=2023):
    print("开始爬取中国大学排名数据...")
    
    first_page_url = f"{base_url}/{year}"
    html = getHTMLText(first_page_url)
    if not html:
        print("无法获取第一页数据")
        return False
    
    soup = BeautifulSoup(html, "html.parser")
    
    fillUnivList(soup)
    print(f"已获取第1页数据，当前总数: {len(allUniv)}")

    total_pages = getTotalPages(soup)
    print(f"检测到总页数: {total_pages}")
    
    for page in range(2, total_pages + 1):
        page_url = f"{base_url}/{year}?page={page}"
        print(f"正在爬取第{page}页: {page_url}")
        
        html = getHTMLText(page_url)
        if not html:
            print(f"第{page}页获取失败，跳过...")
            continue
            
        soup = BeautifulSoup(html, "html.parser")
        fillUnivList(soup)
        print(f"已获取第{page}页数据，当前总数: {len(allUniv)}")
        
        time.sleep(random.uniform(2, 4))
    
    print(f"数据爬取完成，共获取 {len(allUniv)} 所高校信息")
    return True

def printUnivList(num=None):
    if num is None or num > len(allUniv):
        num = len(allUniv)
    
    if num == 0:
        print("没有数据可显示")
        return
    
    tb = PrettyTable()
    tb.field_names = ["排名", "学校名称", "省市", "类型", "总分"]
    tb.align["学校名称"] = "l"  
    tb.align["省市"] = "l"
    tb.align["类型"] = "l"
    
    for i in range(num):
        tb.add_row(allUniv[i])
    
    print(tb)
    print(f"显示前 {num} 条记录，总计 {len(allUniv)} 条记录")

def saveToCSV(filename="university_ranking.csv"):
    import csv
    
    if not allUniv:
        print("没有数据可保存")
        return
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["排名", "学校名称", "省市", "类型", "总分"])
            writer.writerows(allUniv)
        print(f"数据已保存到 {filename}")
    except Exception as e:
        print(f"保存文件时出错: {e}")

def saveToExcel(filename="university_ranking.xlsx"):
    try:
        import pandas as pd
        
        if not allUniv:
            print("没有数据可保存")
            return
        
        df = pd.DataFrame(allUniv, columns=["排名", "学校名称", "省市", "类型", "总分"])
        df.to_excel(filename, index=False)
        print(f"数据已保存到 {filename}")
    except ImportError:
        print("未安装pandas库，无法保存为Excel格式")
        print("请运行: pip install pandas openpyxl")
    except Exception as e:
        print(f"保存Excel文件时出错: {e}")

def searchUniversity(keyword):
    results = []
    for univ in allUniv:
        if keyword in univ[1]:  
            results.append(univ)
    
    if results:
        print(f"找到 {len(results)} 所包含 '{keyword}' 的大学:")
        tb = PrettyTable()
        tb.field_names = ["排名", "学校名称", "省市", "类型", "总分"]
        tb.align["学校名称"] = "l"
        
        for univ in results:
            tb.add_row(univ)
        print(tb)
    else:
        print(f"未找到包含 '{keyword}' 的大学")

def main():
    base_url = 'https://www.shanghairanking.cn/rankings/bcur'
    year = 2023
    
    success = crawlAllPages(base_url, year)
    
    if success and allUniv:
        print("\n" + "="*2)
        print("中国大学排名前30:")
        print("="*2)
        printUnivList(30)
        
        print("\n" + "="*2)
        saveToCSV()
        saveToExcel()

        print("\n" + "="*2)
        print("搜索示例:")
        searchUniversity("北京")
        
        print("\n" + "="*2)
        print(f"数据获取完成，总计 {len(allUniv)} 所高校")
    else:
        print("数据爬取失败")

if __name__ == '__main__':
    main()
