Datasets: 

Q4RealBPP -> Osaba, Eneko; Villar, Esther; V. Romero, Sebastian (2023), “Benchmark dataset and instance generator for Real-World 3dBPP”, Mendeley Data, V1, doi: 10.17632/y258s6d939.1

BED--BPP -> Kagerer F, Beinhofer M, Stricker S, Nüchter A. BED-BPP: Benchmarking dataset for robotic bin packing problems. The International Journal of Robotics Research. 2023;42(11):1007-1014. doi:10.1177/02783649231193048 [BibTeX] [DOI]

![2025-09-18 16-39-561 (1) (1)](https://github.com/user-attachments/assets/2ed9ecb3-44d8-4e05-aba4-db26ea479f40)


Projeye başlarken daha önce yaptığım ama gerçek hayatta kullanımı pek olmayan 2D Bin Packing üzerinden bu sefer 3D yapmalıyım ki gerçek hayatta bir kullanımı olsun diyerek yola çıktım, öncelikle bir veri seti bulmam gerekliydi ve algoritmamı test ettiğim iki adet veri seti buldum.
Öncelikle Genetik Algoritma ile başlayan bu serüven hem hız konusunda hem de farklı sebeplerden ötürü beni kendi algoritmamı yazmaya yönlendirdi. Elde ettiğim modelin gerçekçi bir görüntüsünü görmek istediğim zaman kutuların yanlış yerleştiğini ve uçtuğunu görünce bunlar için de 
kolları sıvadım ve mevcut soruna belirli bir çözüm getiren bir model geliştirmiş oldum. Kişilerin kendi ellerindeki konteyner ve kutular ile denemek isterse diye koduma elle girilen bir kısım da ekledim (kodu çalıştırdığınız zaman bir dosyayı mı yoksa elle mi gireceğinizi soruyor). 
Elimden geldiğince gerçek hayata uyarlı ve bol bol testlerin bulunduğu bu algoritmayı paylaşmayı uygun gördüm. Kısaca algoritmadan bahsedecek olursak:



- Kutuların tüm rotasyonlarını deneyerek yerleşim.

- Çakışma ve destek kontrolü ile kutuların gerçekçi şekilde yerleşmesi.

- Extreme points kullanarak kutular için potansiyel yerleşim noktalarını belirleme.

- Multiprocessing ile çok sayıda deneme yaparak en iyi yerleşimi hızlıca bulma.

- Sonuçları interaktif 3D görselleştirme ile gösterme.


<img width="727" height="596" alt="Ekran görüntüsü 2025-09-18 163333" src="https://github.com/user-attachments/assets/b656b7ed-463a-4476-afed-d0a3ffd2a62c" /><img width="361" height="208" alt="Ekran görüntüsü 2025-09-18 163348" src="https://github.com/user-attachments/assets/6a6c6bb8-570a-430a-bc5f-da832a1d7408" />

<img width="728" height="539" alt="Ekran görüntüsü 2025-09-18 162808" src="https://github.com/user-attachments/assets/1596df21-cfea-48d7-9173-d87b67e5b988" /><img width="394" height="210" alt="Ekran görüntüsü 2025-09-18 163012" src="https://github.com/user-attachments/assets/353b6584-e98f-4ea4-be87-9c46dcfde43b" />



