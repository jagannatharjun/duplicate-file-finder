#include <cassert>
#include <cmath>
#include <filesystem>
#include <string>
#include <string_view>
#include <vector>

#include <cstdio>

#include <gupta/format_io.hpp>
#include <windows.h>

#include <array>
#include <memory>
#include <openssl/sha.h>
#include <unordered_map>

namespace fs = std::filesystem;

class MyFile {
    fs::path m_path;
    std::array<unsigned char, SHA_DIGEST_LENGTH> m_partHash;
    std::array<unsigned char, SHA256_DIGEST_LENGTH> m_fullHash;
    bool m_hasPartHash, m_hasFullHash, m_processed;

  public:
    static size_t PART_HASH_SIZE;
    static std::unique_ptr<unsigned char[]> buf;
    MyFile(fs::path p)
        : m_path{std::move(p)}, m_hasPartHash(false), m_hasFullHash(false),
          m_processed(false) {}

    const auto &path() const { return m_path; }
    const auto &partHash() {
        if (!m_hasPartHash) {
            std::FILE *f = std::fopen(m_path.string().c_str(), "rb");
            auto bs = fread(buf.get(), 1, PART_HASH_SIZE, f);
            SHA1(buf.get(), PART_HASH_SIZE, m_partHash.data());
            fclose(f);
            m_hasPartHash = true;
        }
        return m_partHash;
    }

    const auto &fullHash() {
        if (!m_hasFullHash) {
            std::FILE *f = std::fopen(m_path.string().c_str(), "rb");
            size_t bs;
            SHA256_CTX ctx;
            SHA256_Init(&ctx);
            while ((bs = fread(buf.get(), 1, PART_HASH_SIZE, f)) > 0) {
                SHA256_Update(&ctx, buf.get(), bs);
            }
            SHA256_Final(m_fullHash.data(), &ctx);
            m_hasFullHash = true;
        }
        return m_fullHash;
    }

    void findDuplicates(std::vector<MyFile> &collection) {
        if (m_processed)
            return;
        bool hasDup = false;
        for (auto &f : collection)
            if (!fs::equivalent(f.m_path, m_path) &&
                f.partHash() == partHash() && f.fullHash() == fullHash()) {
                if (!hasDup) {
                    std::wprintf(L"%s", m_path.c_str());
                }
                f.m_processed = hasDup = true;
                std::wprintf(L",\n%s", f.path().c_str());
            }
        if (hasDup)
            puts("\n");
        m_processed = true;
    }
};

size_t MyFile::PART_HASH_SIZE = 64 * 1024;
std::unique_ptr<unsigned char[]> MyFile::buf =
    std::make_unique<unsigned char[]>(MyFile::PART_HASH_SIZE);

bool endswith(std::wstring_view str, std::wstring_view substr) {
    return str.length() >= substr.length() &&
           str.substr(str.length() - substr.length()) == substr;
}

bool wildCardMatching(const wchar_t *fileName, const wchar_t *pattern) {
    while (*fileName && *pattern) {
        switch (*pattern) {
        case L'*':
            pattern++;
            while (*fileName != *pattern) {
                if (*fileName == 0)
                    break;
                fileName++;
            }
            break;
        default:
            if (*fileName != *pattern)
                return false;
        case L'?':
            pattern++, fileName++;
        }
    }
    return *fileName == *pattern;
}

size_t sizeParse(std::wstring_view s) {
    std::wstring_view suffix[] = {L"GB", L"MB", L"KB", L"B"};
    const auto sufCnt = 4;
    for (int i = 0; i < sufCnt; i++) {
        if (endswith(s, suffix[i])) {
            return std::stoull(std::wstring(
                       s.substr(0, s.length() - suffix[i].length()))) *
                   std::pow(1024, sufCnt - i - 1);
        }
    }
    return std::stoull(std::wstring(s));
}

template <typename FileRegister>
void getAllFiles(const std::filesystem::path &arg, FileRegister r) {
    auto resolveDir = [](std::wstring w) { return w; };
    std::wstring dir, pattern;
    if (fs::is_directory(arg)) {
        dir = resolveDir(arg);
        for (auto &&p : fs::recursive_directory_iterator(dir))
            if (p.is_regular_file())
                r(p.path(), p.file_size());
        return;
    }
    dir = resolveDir(arg.parent_path());
    pattern = arg.filename();
    if (pattern.find('*') == pattern.npos &&
        pattern.find('?') == pattern.npos) {
        r(arg, fs::file_size(arg));
        return;
    }
    for (auto &&p : fs::recursive_directory_iterator(dir)) {
        if (p.is_regular_file() &&
            wildCardMatching(p.path().filename().wstring().c_str(),
                             pattern.c_str()))
            r(p.path(), p.file_size());
    }
}

int main() try {
    int argc;
    LPWSTR *argv = CommandLineToArgvW(GetCommandLineW(), &argc);
    assert(sizeParse(L"64KB") == 64 * 1024);
    assert(sizeParse(L"64") == 64);
    assert(sizeParse(L"96MB") == 96 * 1024 * 1024);

    assert(wildCardMatching(L"arara.qbtheme", L"*.qbtheme"));
    assert(wildCardMatching(L"arara.qbtheme", L"*"));
    assert(!wildCardMatching(L"arara.qbtheme", L"*.qb"));
    assert(wildCardMatching(L"", L""));

    assert(fs::is_directory("E:\\Cpp"));
    assert(fs::is_directory("E:\\Cpp\\"));

    std::unordered_map<size_t, std::vector<MyFile>> Files;

    std::size_t MinimumSize = 64 * 1024, MaximumSize = 1024 * 1024 * 1024ull;

    for (int i = 1; i < argc; i++) {
        std::wstring_view arg(argv[i]);
        if (arg == L"--min-size") {
            MinimumSize = sizeParse(argv[++i]);
        } else if (arg == L"--max-size") {
            MaximumSize = sizeParse(argv[++i]);
        } else {
            getAllFiles(arg, [&](const fs::path &p, size_t size) {
                if (size > MinimumSize && size < MaximumSize)
                    Files[size].emplace_back(p);
            });
        }
    }
    for (auto &fs : Files) {
        for (auto &f : fs.second)
            f.findDuplicates(fs.second);
    }
} catch (std::exception &p) {
    std::printf("caught exception(%s), msg: %s\n", typeid(p).name(), p.what());
}
