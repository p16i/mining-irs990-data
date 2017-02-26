#!/bin/bash

data_dir="data"

object_id_pos=9

years=(2013)

output="$data_dir/irs-form-990.txt"

irs_form_990_prefix="https://s3.amazonaws.com/irs-form-990"

# make sure no data in the file
rm $output

# create data directory if it doesn't exist
if [ ! -d $data_dir ]; then
    echo "Creating data directory at '$data_dir'"
    mkdir $data_dir
fi

# retriving index files and extract object ids

for year in "${years[@]}"
do
    dest="$data_dir/$year-index.csv"
    wget -O $dest "$irs_form_990_prefix/index_$year.csv" \
      && sed 1d $dest | cut -d, "-f$object_id_pos" >> $output
done

echo "irs-form-990 object ids are saved to $output"
wc -l $output
echo "done!"
