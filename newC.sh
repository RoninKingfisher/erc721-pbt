if [ $# -ne 1 ] ; then
  echo Usage: newC.sh contractName
  exit 1
fi

mkdir $1 && cp -r ContractTemplate/.gitignore \
      ContractTemplate/.gitattributes \
      ContractTemplate/contracts \
      ContractTemplate/tests \
      $1
exit $?
