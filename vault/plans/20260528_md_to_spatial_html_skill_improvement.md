# md-to-spatial-html Skill 구성 개선 계획

## Summary

`md-to-spatial-html`을 "예쁜 변환 지시문"에서 "반복 실행해도 실패 모드가 줄어드는 파일 변환 skill"로 정리한다. 핵심은 `md-to-spatial-html/SKILL.md`의 충돌 지시를 정리하고, `md-to-spatial-html/assets/template.html`의 placeholder/레이아웃 함정을 줄이며, `md-to-spatial-html/evals/evals.json`에 deterministic 검증 기준을 붙이는 것이다.

## Key Changes

- `md-to-spatial-html/SKILL.md` 지시 정리
  - `no scripts`와 "필요하면 JS 가능" 충돌을 제거하고, v1은 **no JavaScript**로 고정한다.
  - "공간 변환"과 "원문 보존"의 관계를 명확히 한다. 다이어그램은 추가 표현이고, 원문 문장/코드/표/리스트는 HTML 안에 escaped text로 반드시 남긴다.
  - Markdown-origin text는 HTML escape 해야 한다는 규칙을 추가한다. 특히 `<`, `>`, `&`, code fence, inline code를 명시한다.
  - module/file/architecture 섹션은 `figure.modmap > svg`를 요구하되, 해당 섹션의 원문 목록도 보존하도록 쓴다.
  - 완료 체크리스트에 `{{` placeholder 없음, `<script`/`<link` 없음, source footer 있음, peer links 확인, code block count 확인을 추가한다.

- `md-to-spatial-html/assets/template.html` 개선
  - 기본 visible 영역의 예시 placeholder가 그대로 노출되지 않도록 skeleton을 더 안전하게 정리한다.
  - glossary는 acronym이 없으면 섹션 자체를 생략하도록 주석을 바꾼다.
  - scenario matrix는 2열 고정처럼 보이지 않게 CSS grid 예시를 범용 형태로 바꾼다.
  - SVG module map 예시는 긴 파일명을 처리할 수 있도록 `<text>`를 짧은 label 중심으로 두고, 상세 경로는 아래 원문/표현 텍스트에 남기라는 주석을 추가한다.
  - CSS의 negative letter-spacing은 제거해 현재 frontend 가이드와 충돌하지 않게 한다.

- deterministic 검증 스크립트 추가
  - `md-to-spatial-html/scripts/validate_output.py`를 새로 만든다. Python stdlib만 사용한다.
  - CLI 형태: `python scripts/validate_output.py --source <md> --html <html> [--peer <html>] [--require-modmap] [--forbid-svg]`.
  - 검사 항목: `.md` 존재, `.html` 존재, `{{` 없음, 외부 `<link>`/`<script src>`/`http(s)://` asset 없음, footer source path 있음, source headings에 대응하는 anchors 있음, code fence 개수 이상 `<pre><code>` 있음.
  - `--require-modmap`이면 `figure class="modmap"`와 `<svg>`가 있어야 한다.
  - `--forbid-svg`이면 `<svg>`가 없어야 한다.

- `md-to-spatial-html/evals/evals.json` 강화
  - `expected_output`을 사람이 읽는 문장만이 아니라 객관 조건 중심으로 바꾼다.
  - 각 eval에 `assertions` 필드를 추가한다.
  - 기존 세 케이스는 유지한다.
  - `test1_rich_plan.md`는 `require_modmap: true`, `test2_plan.md`/`test2_detail.md`는 peer link/footer 확인, `test3_rfc.md`는 `forbid_svg: true`로 둔다.

## Test Plan

- `skills-ref validate md-to-spatial-html`를 실행한다. 도구가 없으면 frontmatter 수동 체크로 대체한다.
- `python md-to-spatial-html/scripts/validate_output.py --help`가 성공하는지 확인한다.
- 검증 스크립트용 최소 fixture HTML을 임시 디렉터리에 만들어 positive/negative 동작을 확인한다.
- 기존 eval 입력 기준으로 다음 실패가 잡히는지 확인한다.
  - placeholder 잔존
  - footer 누락
  - file layout인데 modmap 없음
  - prose RFC에 SVG 조작 생성
  - peer link 누락
  - code block 누락

## Assumptions

- 이번 작업은 skill load 문제 수정이 아니라 구성 품질 개선이다.
- 자동 검증 스크립트를 포함한다.
- HTML 생성 자체를 완전 자동화하는 변환기는 만들지 않는다. 이 skill은 여전히 agent가 `template.html`을 기반으로 작성하되, 실패 조건을 더 명확히 검증하게 만든다.
- v1 범위에서는 JavaScript를 허용하지 않고, 모든 시각화는 CSS와 inline SVG만 사용한다.
