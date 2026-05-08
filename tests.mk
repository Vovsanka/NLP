#!/usr/bin/env -S make -f

TESTDIR := $(CURDIR)/tests
TESTRUN := $(TESTDIR)/run
DATA := $(TESTDIR)/data
PROG := $(CURDIR)/pcfg_tool

export TESTDIR TESTRUN DATA PROG

BATS := $(shell which bats 2> /dev/null || echo "$(TESTDIR)/bats-dist/bats")

TESTS := $(notdir $(basename $(wildcard $(TESTDIR)/*.bats)))

.PHONY: tests prepare_testrun $(TESTS) clean

tests: prepare_testrun $(TESTS)

prepare_testrun:
	@[ ! -d "$(TESTRUN)" ] || rm -r "$(TESTRUN)"
	@mkdir "$(TESTRUN)"

$(TESTS):
	@echo $$'\n'Testing $@
	@cd "$(TESTRUN)" && "$(BATS)" "$(TESTDIR)/$@.bats" || true

clean:
	-rm -r "$(TESTRUN)"

.NOTPARALLEL:
