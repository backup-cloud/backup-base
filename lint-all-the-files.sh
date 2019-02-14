#!/bin/bash
#
# based on https://github.com/mikedlr/mdd-ansible-dev/blob/master/git-hooks/pre-commit
#
# copyright Michael De La Rue (c) 2017
# copyright Michael De La Rue (c) 2018  - paid work for Paddle.com
#
# This file is licensed under the AGPLv3



if [ -z "${SHELLCHECK}" ]
then
    SHELLCHECK=shellcheck
fi

find . \( -type d \( -name venv -o -name .git -o -iname '*py*cache*' \) -prune -false \) -o -type f | (
    failcount=0
    # substatus=0
    while read -r file
    do
	case "$file" in
	    ./features*/steps/*.py)
		echo "flake8 checking $file:"
		# T499 seems to be a mypy failure
		flake8 --ignore=W503,E402,E501,F811,T484,T499 "$file" --max-line-length=99 --builtins=given,when,then &&
		    ! grep --with-filename --line-number 'pdb.set_trace\|FIXME' "$file" ;;
	    *.py)
		echo "flake8 checking $file:"
		# probably an effective bug - T484 is needed because otherwise it fails
		# claiming "Module '__future__' has no attribute 'annotations'"
		flake8 --ignore=W503,E402,E5b01,T484,T499 "$file" --max-line-length=99 &&
		    ! grep --with-filename --line-number 'pdb.set_trace\|FIXME' "$file" ;;
	    *.yaml | *.yml )
		echo "yamllint checking $file:"
		yamllint --format parsable "$file" -d "line-length: {max: 70}";;
	    *.sh)
		echo "shellcheck checking $file:"
		${SHELLCHECK} -f gcc "$file";;
	    *.enc | *.env | .gitignore)
		true;; # we explicitly have nothing to verify
	    '#*' | *~ | *.pyc | *.retry )
		true;;
	    *)
		echo "no rule for $file";;
	esac
	newstat=$?
	if [[ "$newstat" -gt "$status" ]]
	then
	    ((failcount++))
	#    substatus=$newstat
	fi
    done
    exit $failcount )

status=$?

if [[ "$status" -gt 0 ]]
then
    echo "linting failed on $status files" 
    exit 1
fi
