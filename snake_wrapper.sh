#temp_list="${@:13}"
#cities="${temp_list}"
snakemake --config sit_rep_name=$1 county_name="${2}" city_name="${3}" db=$4 county_shapes=$5 county_shapes_name=$6 city_shapes=$7 city_shapes_name=$8 repo=$9 start_date=${10} end_date=${11} path=${12} min_lat=${13} max_lat=${14} min_lon=${15} max_lon=${16}  --cores 1 
