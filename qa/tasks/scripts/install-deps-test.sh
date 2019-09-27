# install-deps-test.sh
#
# always gets two args:
#     git repo (e.g. "https://github.com/ceph/ceph.git")
#     git branch (e.g. "master")
#

set -ex

echo "install-deps-test.sh: dump contents of /etc/os-release"
cat /etc/os-release

echo "install-deps-test.sh: rpm -qa before"
RPM_QA_BEFORE=$(mktemp)
rpm -qa | sort | sed 's/\-[[:digit:]].*$//' | tee $RPM_QA_BEFORE

GIT_REPO=$1
GIT_BRANCH=$2
echo "install-deps-test.sh: cloning git repo $GIT_REPO branch $GIT_BRANCH"
git clone $GIT_REPO
cd ceph
git checkout $GIT_BRANCH
source install-deps.sh

echo "install-deps-test.sh: rpm -qa after"
RPM_QA_AFTER=$(mktemp)
rpm -qa | sort | sed 's/\-[[:digit:]].*$//' | tee $RPM_QA_AFTER

echo "install-deps-test.sh: diff before after"
echo "WWWW: DIFF BEGIN"
diff --old-line-format="" --unchanged-line-format="" $RPM_QA_BEFORE $RPM_QA_AFTER || true
echo "WWWW: DIFF END"
