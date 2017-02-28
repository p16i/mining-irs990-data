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
One of the challenges here is retrieving and extracting relevant attributes from those documents. For `2013`, we have `153560` documents to be extracted.
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
$ awk '{print}' data/success/* > irs900-data.txt
# compute yoy as we want
$ scala compute-yoy.scala irs900-data.txt
# output shown at `Result` section
```
With `batch-size` at `100` documents, each invocation completes within `1` minutes. During job submission, `submit-job.py` pauses  `30s` at every `50` batches, this submission process takes around `23` minutes to complete. Once data is available on `s3`, collecting the intermediate results and computing YoY are rather fast. In total, the whole pipeline takes approximately `25` minutes.

## Result
```
Loading 147356 items
Total national average YoY Revenue in 2013 : 34.639212920080034
---- Average YoY by State --
NC : 318.60719422967225
NE : 308.701946605048
IN : 150.25144831514362
CA : 125.07959038330728
OK : 103.22254941079741
DE : 71.54795428152978
MA : 52.72399318116768
IL : 47.515297059224544
NJ : 23.98263837200653
MI : 23.41380133405708
AL : 20.912682611705417
OH : 20.652818066415396
MD : 18.35140101124933
CO : 17.053739995760235
AR : 12.25116600870379
NY : 8.881116596548107
MO : 8.08202583644619
OR : 7.656925616257503
AZ : 6.416831676298093
MS : 3.602606028579922
FL : 3.56920731725728
TX : 3.0077091426598157
UT : 2.923809717661468
DC : 2.3483057285901996
HI : 2.015361697527572
TN : 1.63287998105445
GA : 1.46905019587949
SC : 1.4416878351295974
WV : 1.4393619604675878
RI : 1.4369876045082364
WI : 1.3751423003482992
WA : 1.180045944914481
MT : 1.1474964783690997
CT : 0.938726844909962
NV : 0.886680320719267
IA : 0.8501203292706007
PA : 0.8369782590084921
KS : 0.7122539708247478
KY : 0.6558975852242328
LA : 0.6179313798123884
NH : 0.5875247865435802
AK : 0.5751936713763923
ME : 0.5454945479434592
VA : 0.5259495522653972
WY : 0.47676920338360385
MN : 0.44889900194462673
ID : 0.41917504705904945
SD : 0.36503914844045254
VT : 0.33266455824793173
RESTRICTED : 0.2966393490186133
ND : 0.2752861964771789
NM : 0.1888994693692287
VI : 0.15531902812975973
PR : 0.029806059394842235
```

# Improvements
1. Parallel invoke lambda service to reduce job submission time.
2. Running-time of each invocation can be reduced using same technique.
3. Incorporate retrying falied documents into the process
