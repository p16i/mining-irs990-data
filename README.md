## Mining IRS900 Data

[IRS900](https://aws.amazon.com/public-datasets/irs-990/) contains financial information about nonprofit organizations gathered by United States Internal Revenue Service. This project aims to build a prototype for mining the dataset. Particularly, I am interested in answering the following questions for 2013:
1. What was the (approximate) average Year-over-Year revenue growth nationally
2. What was the (approximate) average Year-over-Year revenue growth by State

where Year-over-Year(YoY) revenue is computed by:
```
 (current_year_revenue - previous_year_revenue) /  previous_year_revenue
```

## Overview of the dataset
The data is split into yearly basis. For each year, it has an index file that contains all `OBJECT_ID`s of irs900 forms submitted on that year.

#### IRS900 Form
The form is served as `XML` document. It contains basic information of each organization, such as name, and state, and financial situation for that year. Details of the financial information are different for each variant of the form. The form has  5 variants, namely `990`, `990EO`, `990EZ`, `990O` and `990PF`. In this case, only `990` and `990O` are revelant to the questions as they have `TotalRevenuePriorYear` and `TotalRevenueCurrentYear`.

## System Overview
One of the challenges here is retrieving and extracting relevant attributes from those documents. For `2013`, we have `137789` documents to be extracted.
```
# download the index file
$ wget https://s3.amazonaws.com/irs-form-990/index_2013.csv
# count 990 and 990EO documents 
$ cat index_2013.csv | grep -e '990,' -e '990O' | wc -l
> 153560
```
Clearly, this process is time-consuming and dominate performance of the computation pipeline. Thus, we need to do it in distributed setting to fasten the whole pipeline.

Given this reasoning, the system has components as shown in the figure below.
![](http://i.imgur.com/Sm6bzOd.png)
1. A python script `submit-job.py` is created to build batches of documents. It hands each batch to a λ invocation and stop for sometimes after `k` batches to prevent exceeding concurrency limit of λ-service, [more info](http://docs.aws.amazon.com/lambda/latest/dg/concurrent-executions.html).
```
$ python submit-job.py index_2013.csv
```
2. Each invocation executes `lambda-code.py` which extracts relevant attributes that it is given and saves the result to s3.
3. Once everything is finished, the results from s3 are retrieved by using [`aws-cli`](https://aws.amazon.com/cli/) comand processed as  follows :
```
# copy files to local
$ aws s3 cp s3://irs900-collection data --recursive
# merge results into 1 file
$ cat data/success/* > irs900-data.txt
# compute yoy as we want
$ scala compute-yoy.scala irs900-data.txt
# output shown at `Result` section
```
With `batch-size` at `100` documents, each invocation completes within `1` minutes. During job submission, `submit-job.py` pauses  `30s` at every `50` batches, this submission process takes around `8` minutes to complete. Once data is available on `s3`, collecting the intermediate results and computing YoY are rather fast. The computation part takes around `2s`. In total, the whole pipeline takes approximately `10` minutes.

## Result
```
Loading 147358 items
Total national average YoY Revenue in 2013 : 34.638726590437756
---- Average YoY by State --
NC : 318.6071942296721
NE : 308.7019466050483
IN : 150.251448315144
CA : 125.0903723046981
OK : 103.22254941079733
DE : 71.5479542815299
MA : 52.72399318116728
IL : 47.515297059224665
NJ : 23.982491651728992
MI : 23.409018210162873
AL : 20.912682611705467
OH : 20.659263057170232
MD : 18.351401011249273
CO : 17.05373999576024
AR : 12.25116600870379
NY : 8.88042408048016
MO : 8.084556411508691
OR : 7.656925616257525
AZ : 6.416831676298082
MS : 3.6026060285799226
FL : 3.5696352369904676
TX : 3.0073027899586293
UT : 2.9238097176614666
DC : 2.348305728590196
HI : 2.0153616975275725
TN : 1.6328799810544494
GA : 1.4690501958794917
SC : 1.4416878351295968
RI : 1.4369876045082344
WV : 1.435868252906046
WI : 1.3755225352533456
WA : 1.1800459449144853
MT : 1.1485953211638789
CT : 0.9387268449099588
NV : 0.8866803207192667
IA : 0.8501203292706004
PA : 0.8369782590084901
KS : 0.7119448925136436
KY : 0.655897585224232
LA : 0.6179313798123879
NH : 0.5875247865435805
AK : 0.5751936713763922
ME : 0.5454945479434595
VA : 0.5258111903548891
WY : 0.4758089789192157
MN : 0.4487571551013451
ID : 0.4191750470590498
SD : 0.3650391484404526
VT : 0.3326645582479315
RESTRICTED : 0.2966393490186133
ND : 0.2752861964771788
NM : 0.18889946936922838
VI : 0.1553190281297597
PR : 0.029806059394842228
```

# Improvements
1. Parallel invoke lambda service to reduce job submission time.
2. Running-time of each invocation can be reduced using same technique.
