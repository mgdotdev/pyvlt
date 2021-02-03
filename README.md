# vlt

vlt is an command line tool meant for storing username and password information within an encrypted SQLite database. Database files are localized and transportable, allowing users to archive, export, and link vlt's .db files with any other instance of vlt.

Things you can do with vlt:

- access vlt directly from command line
- get, add, edit, and remove vlt entries
- search vlt by common source, username, and password entries
- have multiple vlt tables in single vlt db, each with separate encryption key/salt codes
- store you db files outside vlt, such as in a private git repository
- link vlt to external vlt db file, such as one on USB drive or in git
- archive db's to keep contents in separate db files
- consume/dump unencrypted csv files to/from vlt

Specific use cases for the tool can be found by installing vlt and calling the help menu via `vlt --help`

## Example
with vlt installed, we can add our first entry:

`vlt add`

this will prompt vlt to ask for your vlt key:

- note: while you *can* pass -k `<KEY>` to vlt, this is **not** recommended, and is only used herein for demonstration purposes.
```
Please enter your vlt key:
$ test
```

since no source, username, or password were initially provided, vlt will ask for your credentials:

```
specify source:
$ fizz

specify username:
$ buzz

specify password:
$ fizzbuzz
```

optionally, we could have specified these from the command line, like:
`vlt add -s fizz -u buzz -p fizzbuzz`
any parameter not included from CLI will be requested by vlt (best not to store passwords from CLI so they don't persist in shell history).

to see our vlt entry, we can call `get` so to query vlt: 

`vlt get`

since no get parameter was provided, vlt will ask for one:
```
specify search term(s):
 1) index        3) username
 2) source       4) password
$ 1

specify index:
$ 0

   source username  password
0   fizz     buzz  fizzbuzz
```
alternatively we can specify search parameters from the command line:

`vlt get -i 0`

searching across multiple terms returns the INNER JOIN of the parameters:

```
vlt add -s this -u buzz -p test -k test
vlt add -s bam -u buzz -p test -k test
vlt get -p test -u buzz

   source username  password
1   this     buzz  test
2   bam      buzz  test
```

entries can be edited and/or removed via the entry index

```
vlt edit -i 1 -s bim -k test
vlt get -i 1 -k test

   source username password
1    bim     buzz     test
```

with vlt we can autogenerate strong passwords using `vlt make`. See `vlt --help` for formatting specifics under the [make] command.

```
vlt make -s fizzbuzz -u michael -fmt v --via alphanumeric --omit 012345 --length 50 -k test

8.
  SOURCE: fizzbuzz
USERNAME: michael
PASSWORD: tM8eRDwTDwyHkhKRWUmMTNAeRv6OlseFXTKthNLDHlCgPm8GwT
```

our db file can be exported to a local file directory:
```
vlt export /mnt/d/my_vlt.db
```

and vlt can link to this file for db I/O.

```
vlt link /mnt/d/my_vlt.db
vlt get -s fizzbuzz -k test

8.
  SOURCE: fizzbuzz
USERNAME: michael
PASSWORD: tM8eRDwTDwyHkhKRWUmMTNAeRv6OlseFXTKthNLDHlCgPm8GwT
```

in vlt, the help menu can be accessed by calling `vlt --help`. The help section for each individual command can also be returned by calling `vlt <CMD> --help`

```
$ vlt edit --help

add/edit/get/remove
===================

 KWARGS
- [-i] <INDEX> - relative index of entry to select
- [-s] <SOURCE> - source to search against in db
- [-u] <USERNAME> - username to search against in db
- [-p] <PASSWORD> - password to search against in db

```