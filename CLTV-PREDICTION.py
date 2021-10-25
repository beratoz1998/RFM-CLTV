# PROJE: BGNBD & GG ile CLTV Tahmini ve Sonuçların Uzak Sunucuya Gönderilmesi

# GÖREV 1 :
#  1. 2010-2011 UK müşterileri için 6 aylık CLTV prediction yapınız.
#pip install Lifetimes
import datetime as dt
import pandas as pd
from lifetimes import BetaGeoFitter
from lifetimes import GammaGammaFitter

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)
pd.set_option('display.float_format', lambda x: '%.5f' % x)

df_ = pd.read_excel("ÖDEV/online_retail_II.xlsx", sheet_name="Year 2010-2011")
df = df_.copy()

df = df[df["Country"] == "United Kingdom"]
df.dropna(inplace=True)
df = df[~df["Invoice"].str.contains("C", na=False)]
df = df[df["Quantity"] > 0]

df.describe().T

def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit


def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit


replace_with_thresholds(df, "Quantity")
replace_with_thresholds(df, "Price")

df.describe().T

df["TotalPrice"] = df["Quantity"] * df["Price"]

today_date = dt.datetime(2011, 12, 11)


cltv_df = df.groupby('Customer ID').agg({'InvoiceDate': [lambda date: (date.max() - date.min()).days,
                                                         lambda date: (today_date - date.min()).days],
                                         'Invoice': lambda num: num.nunique(),
                                         'TotalPrice': lambda TotalPrice: TotalPrice.sum()})

cltv_df.head()
cltv_df.columns = cltv_df.columns.droplevel(0)

# değişkenlerin isimlendirilmesi
cltv_df.columns = ['recency', 'T', 'frequency', 'monetary']
cltv_df.head()

# monetary değerinin satın alma başına ortalama kazanç olarak ifade edilmesi
cltv_df["monetary"] = cltv_df["monetary"] / cltv_df["frequency"]

# monetary sıfırdan büyük olanların seçilmesi
cltv_df = cltv_df[cltv_df["monetary"] > 0]
cltv_df.head()

# BGNBD için recency ve T'nin haftalık cinsten ifade edilmesi
cltv_df["recency"] = cltv_df["recency"] / 7
cltv_df["T"] = cltv_df["T"] / 7

# frequency'nin 1'den büyük olması gerekmektedir.
cltv_df = cltv_df[(cltv_df['frequency'] > 1)]

cltv_df.head()

#lifetime kütüphanesini kullanacağız.
bgf = BetaGeoFitter(penalizer_coef=0.001)
bgf.fit(cltv_df['frequency'],cltv_df['recency'],cltv_df['T'])


cltv_df["expected_purc_1_week"] = bgf.predict(1,cltv_df['frequency'],cltv_df['recency'],cltv_df['T'])

cltv_df["expected_purc_1_month"] = bgf.predict(4,cltv_df['frequency'],cltv_df['recency'],cltv_df['T'])

cltv_df.head()


ggf = GammaGammaFitter(penalizer_coef=0.01)
ggf.fit(cltv_df['frequency'], cltv_df['monetary'])

ggf.conditional_expected_average_profit(cltv_df['frequency'],cltv_df['monetary']).head(10)

ggf.conditional_expected_average_profit(cltv_df['frequency'],cltv_df['monetary']).sort_values(ascending=False).head(10)

cltv_df["expected_average_profit"] = ggf.conditional_expected_average_profit(cltv_df['frequency'],cltv_df['monetary'])

cltv_df.sort_values("expected_average_profit", ascending=False).head(20) #ortalama kar getirilerine göre sıraladık.
cltv_df.head()


cltv = ggf.customer_lifetime_value(bgf,cltv_df['frequency'],cltv_df['recency'],cltv_df['T'],cltv_df['monetary'],
                                   time=6,  # 6 aylık
                                   freq="W",  # T'nin frekans bilgisi.
                                   discount_rate=0.01)

cltv.head()

cltv.shape
cltv = cltv.reset_index()
cltv.head()

cltv.sort_values(by="clv", ascending=False).head(50)
cltv_final = cltv_df.merge(cltv, on="Customer ID", how="left") #soldan birleştirme işlemi gerçekleştirdik.
cltv_final.sort_values(by="clv", ascending=False).head()
cltv_final.sort_values(by="clv", ascending=False)[10:30] #slicing yöntemi ile 10-30 arasını aldık


#1-100 arası Transform
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range=(1, 100))
scaler.fit(cltv_final[["clv"]])
cltv_final["SCALED_CLTV"] = scaler.transform(cltv_final[["clv"]])
cltv_final.sort_values(by="clv", ascending=False)[10:30]
cltv_final.head()


#  2. Elde ettiğiniz sonuçları yorumlayıp üzerinde değerlendirme yapınız.



# GÖREV 2
# 1. 2010-2011 UK müşterileri için 1 aylık ve 12 aylık CLTV hesaplayınız.

cltv1 = ggf.customer_lifetime_value(bgf,cltv_df['frequency'],cltv_df['recency'],cltv_df['T'],cltv_df['monetary'],
                                   time=1,  # 1 aylık
                                   freq="W",  # T'nin frekans bilgisi.
                                   discount_rate=0.01)

cltv1_final = cltv_df.merge(cltv1, on="Customer ID", how="left")
cltv1_final.sort_values(by="clv", ascending=False).head(10)


cltv12 = ggf.customer_lifetime_value(bgf,cltv_df['frequency'],cltv_df['recency'],cltv_df['T'],cltv_df['monetary'],
                                   time=12,  # 12 aylık
                                   freq="W",  # T'nin frekans bilgisi.
                                   discount_rate=0.01)

cltv12_final = cltv_df.merge(cltv12, on="Customer ID", how="left")
cltv12_final.sort_values(by="clv", ascending=False).head(10)

# 2. 1 aylık CLTV'de en yüksek olan 10 kişi ile 12 aylık'taki en yüksek 10 kişiyi analiz ediniz. Fark var mı?
# Varsa sizce neden olabilir?

cltv1_final.sort_values("clv", ascending=False).head(10)
cltv12_final.sort_values("clv", ascending=False).head(10)

#Kişiler konusunda fark yok. aynı kişiler sadece 1 aylık ve 12 aylık sıralama yaptığımız zaman yerleri değişmiş.

# GÖREV 3

# 1. 2010-2011 UK müşterileri için 6 aylık CLTV'ye göre tüm müşterilerinizi 4 gruba (segmente) ayırınız ve grup isimlerini veri setine ekleyiniz.

cltv = ggf.customer_lifetime_value(bgf,cltv_df['frequency'],cltv_df['recency'],cltv_df['T'],cltv_df['monetary'],
                                   time=6,  # months
                                   freq="W",  # T haftalık
                                   discount_rate=0.01)

cltv_final = cltv_df.merge(cltv, on="Customer ID", how="left")
cltv_final.head()

scaler = MinMaxScaler(feature_range=(1, 100))
scaler.fit(cltv_final[["clv"]])
cltv_final["SCALED_CLTV"] = scaler.transform(cltv_final[["clv"]])

cltv_final["cltv_segment"] = pd.qcut(cltv_final["SCALED_CLTV"], 4, labels=["D", "C", "B", "A"])
cltv_final["cltv_segment"].value_counts()
cltv_final.head()

cltv_final.groupby("cltv_segment")[["expected_purc_1_month", "expected_average_profit", "clv", "SCALED_CLTV"]].agg(
    {"count", "mean", "sum"})

# 2. CLTV skorlarına göre müşterileri 4 gruba ayırmak mantıklı mıdır?

#Elbette mantıklıdır. Müşterileri göz önünde bulundurmak yerine 4 grubu göz önünde bulundurup reklam çalışmaları , kampanyaları \
#bu 4 gruba ayrı ayrı yapabiliriz. örneğin frequency ve monetary'si yüksek olan biri zaten bizden memnundur. Bir kampanya yapılacaksa \
# bu gruptakielre kampanya yapmasan bile bunlar bizim için şampiyon kategorisinde. Bizim amacımız B,C,D gruplarını A grubuna yetiştirmek olmalıdır.


#3. 4 grup içerisinden seçeceğiniz 2 grup için yönetime kısa kısa 6 aylık aksiyon önerilerinde bulununuz.

#A grubu en yüksek kategorimiz, B ve C yi A grubuna yetiştirmeyi öncelikli hedefimiz haline getirmeliyiz.
#Bu gruplar için kampanyalar düzenleyebiliriz.
# Örneğin ; A grubu ortalama kâr oranı kişi başı 608 birim. B grubu 370 , C grubu 278 birim.

cltv_final = cltv_final.reset_index()
cltv_final["Customer ID"] = cltv_final["Customer ID"].astype(int)


#Veritabanina uzaktan bağlantı için:
# MySQL 8.0.26
#host: 34.88.156.118
#port: 3306
#username: group_02
#password: hayatguzelkodlarucuyor

cltv_final.to_sql(name='cltv_prediction', con=conn, if_exists='replace', index=False)
