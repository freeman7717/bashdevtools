#!/bin/bash

if [ -z "$1" ]; then
    echo "Имя пустое или не передано."
    echo "Пример: $0 sales.txt"
    exit 1
fi

file="$1"

bestday=""
bestsum=0
totalsum=0

while IFS= read -r line; 
do
    # проверка числа полей
    if [ "$(echo "$line" | awk '{print NF}')" -ne 5 ]; then
        echo "Нарушена структура строки:"
        echo "$line"
        exit 1
    fi

    read -r dt dow item price amount <<< "$line"
    
    if [ -z $bestday ];
    then 
		bestday="${dt}_${dow}"
		current_dt="${dt}_${dow}"
		sumofsales=0
    fi

	if [ $current_dt = "${dt}_${dow}" ];
	then
		total=$(echo "scale=3; $price * $amount" | bc)
		sumofsales=$(echo "scale=3; $sumofsales + $total" | bc)
		totalsum=$(echo "scale=3; $totalsum + $total" | bc)
	else
		# поиск максимума
		if (( $(echo "$sumofsales > $bestsum" | bc -l) )); 
		then
			bestsum=$sumofsales
			bestday=$current_dt
		fi
		current_dt="${dt}_${dow}"
		sumofsales=0
    fi

done < <(sort -k1 "$file")

echo "Общая сумма продаж: $totalsum"

echo "Лучший день: $bestday"

echo "Максимальная сумма: $bestsum"


bestitem=""
bestamount=0
sumofsales=0

while IFS= read -r line; do

    read -r dt dow item price amount <<< "$line"

    if [ -z $bestitem ];
    then 
		bestitem="$item"
		current_item="$item"
		itemamount=0
		sumofitem=0
    fi

    if [ $current_item = "$item" ];
	then
	    ((itemamount++))
		total=$(echo "scale=3; $price * $amount" | bc)
		sumofitem=$(echo "scale=3; $sumofitem + $total" | bc)
	else
		# поиск максимума
		if [ $itemamount -gt $bestamount ]; 
		then
			bestitem=$current_item
			bestamount=$itemamount
			sumofsales=$sumofitem
		fi
		current_item="$item"
		itemamount=0
		sumofitem=0
    fi

done < <(sort -k3 "$file")
echo "Популярный товар: $bestitem (количество проданных единиц: $bestamount, сумма продаж: $sumofsales)
"
