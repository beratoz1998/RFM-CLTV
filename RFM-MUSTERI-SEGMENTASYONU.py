# PROJE: RFM ile Müşteri Segmentasyonu

# Görev 1: Veriyi Anlama ve Hazırlama


# 2. Veri setinin betimsel istatistiklerini inceleyiniz.
# 3. Veri setinde eksik gözlem varmı? Varsa hangi değişkende kaç tane eksik gözlem vardır?
# 4. Eksik gözlemleri veri setinden çıkartınız. Çıkarma işleminde ‘inplace=True’parametresini kullanınız.
# 5. Eşsiz ürün sayısı kaçtır?
# 6. Hangi üründen kaçar tane vardır?
# 7. En çok sipariş edilen 5 ürünü çoktan aza doğru sıralayınız.
# 8. Faturalardaki ‘C’ iptal edilen işlemleri göstermektedir. İptal edilen işlemleri veri setinden çıkartınız.
# 9. Fatura başına elde edilen toplam kazancı ifade eden ‘TotalPrice’ adında bir değişken oluşturunuz.

import matplotlib.pyplot as plt
import datetime as dt
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', lambda x: '%.5f' % x)

# 1. Online Retail II excelindeki 2010-2011 verisini okuyunuz. Oluşturduğunuz dataframe’in kopyasını oluşturunuz.
df_ = pd.read_excel("ÖDEV/online_retail_II.xlsx", sheet_name="Year 2010-2011")
df = df_.copy()

# 2. Veri setinin betimsel istatistiklerini inceleyiniz.
df.head()
df.describe().T
df["Price"].mean()
df["Quantity"].mean()
df["Price"].median()
df["Quantity"].median()

df["Price"][df["Price"]<1000].hist(bins=50)
plt.show()

# 3. Veri setinde eksik gözlem varmı? Varsa hangi değişkende kaç tane eksik gözlem vardır?
df.isnull().sum()

# 4. Eksik gözlemleri veri setinden çıkartınız. Çıkarma işleminde ‘inplace=True’parametresini kullanınız.
df.dropna(inplace=True)

# 5. Eşsiz ürün sayısı kaçtır?
df["Description"].nunique()


# 6. Hangi üründen kaçar tane vardır?
df["Description"].value_counts()

df.groupby("Description").agg({"Description": "count"})

# 7. En çok sipariş edilen 5 ürünü çoktan aza doğru sıralayınız.
df.groupby("Description").agg({"Quantity": "sum"}).sort_values("Quantity", ascending=False).head(5)

# 8. Faturalardaki ‘C’ iptal edilen işlemleri göstermektedir. İptal edilen işlemleri veri setinden çıkartınız.
df = df[~df["Invoice"].str.contains("C", na=False)]

# 9. Fatura başına elde edilen toplam kazancı ifade eden ‘TotalPrice’ adında bir değişken oluşturunuz.
df["TotalPrice"] = df["Quantity"] * df["Price"]

# Görev 2: RFM Metriklerinin Hesaplanması

df["InvoiceDate"].max() #max. günün 2011-11-09 olduğunu gördük.
today_date = dt.datetime(2011, 12, 11)

rfm = df.groupby('Customer ID').agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                     'Invoice': lambda num: num.nunique(),
                                     'TotalPrice': lambda TotalPrice: TotalPrice.sum()})

rfm.columns = ['recency', 'frequency', 'monetary']
rfm = rfm[rfm["monetary"] > 0]

# Görev 3: RFM Skorlarının Oluşturulması ve Tek Bir Değişkene Çevrilmesi

rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
#qcut fonksiyonu ile küçükten büyüğe sırala 5 e böl en küçüğüne 5 en büyüğüne 1 ver. (son alış-veriş yapan daha değerli olduğundan küçük olana 5 verdik.)
rfm["frequency_score"] = pd.qcut(rfm['frequency'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

rfm["RFM_SCORE"] = (rfm['recency_score'].astype(str) +
                    rfm['frequency_score'].astype(str))

# Görev 4: RFM Skorlarının Segment Olarak Tanımlanması

seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}

rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
rfm['segment'].head

#Görev 5 : Önemli bulduğunuz 3 segmenti seçiniz. Bu üç segmenti;
#Hem aksiyon kararları açısından,
# Hem de segmentlerin yapısı açısından (ortalama RFM değerleri) yorumlayınız.


rfm[["segment", "recency", "frequency", "monetary"]].groupby("segment").agg(["mean", "count"])

#cant_loose
#need_attention
#at_Risk

new_df = pd.DataFrame()
new_df["loyal_customers"] = rfm[rfm["segment"] == "loyal_customers"].index
new_df.head()

new_df.to_csv("loyal_customers.csv")