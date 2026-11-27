## 第6回 解答

### 演習

- STEP 1 のツールの名前：
  - 通常のエージェント：`search_materials`
  - MCPエージェント：`glossary_search_glossary`
  - fetchサーバー追加後：`glossary_search_glossary`、`fetch_fetch`
  - AWSサーバー追加後：`glossary_search_glossary`、`fetch_fetch`、`aws_aws___read_documentation`、`aws_aws___search_documentation`、`aws_aws___list_regions`、`aws_aws___get_regional_availability`、`aws_aws___retrieve_skill`

- STEP 2 の `[tool call]`：
  `glossary_search_glossary({'query': '3レベル'})`

- STEP 3 の `[tool call]`：
  `fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`

- STEP 4 の `[tool call]`：
  `aws_aws___search_documentation({'search_phrase': 'Amazon S3 バージョニング 概要'})`

  `aws_aws___search_documentation({'search_phrase': 'What is S3 Versioning Amazon Simple Storage Service'})`

- 気づき・疑問：
  通常のエージェントではPython関数を直接ツールとして登録していたが、MCPエージェントではサーバーからツールの名前、説明文、引数を受け取っていた。モデルから見ると、どちらも同じ形式のツールとして渡されていた。

  MCPツール名には、`glossary_search_glossary` や `fetch_fetch` のように「サーバー名_ツール名」という接頭辞が付いた。これにより、複数のMCPサーバーに同名のツールがあっても区別できると分かった。

  glossaryとfetchはCodespaces内でコマンドから起動されたが、AWS Knowledge MCPサーバーは外部URLへ接続して利用した。設定ファイルへ接続先を追加するだけで、エージェント本体を変更せず、モデルに見えるツールを1個から7個へ増やすことができた。

  STEP 2では、用語集ツールを1回呼び出し、モデル応答は2回だった。STEP 3でもfetchツールを1回呼び出し、モデル応答は2回だった。STEP 4ではAWSの検索ツールを、検索語を変えて2回呼び出し、モデル応答は3回だった。モデルは最初の検索結果だけでは回答せず、より適切な英語の検索語でもう一度検索したと考えられる。

  一方、外部MCPサーバーでは、質問やツールの引数が外部の提供者へ送られる。また、fetchサーバーには内部アドレスへのアクセスやrobots.txtに関するリスクと制限があるため、提供元、公開されるツール、送信される情報を確認してから設定へ追加する必要がある。：

## 宿題

#### 基礎

- 取り組んだレベル：基礎

- やったこと：
  `app/mcp_server.py` に `server.tool()(tools.get_lecture_summary)` を追加し、既存の `get_lecture_summary` 関数をMCPツールとして公開した。MCPエージェント側のコードや設定ファイルは変更せず、サーバー側の公開ツールだけを増やした。

- 結果：
  変更前は用語集サーバーが公開するツールは `glossary_search_glossary` の1個だったが、変更後は `glossary_get_lecture_summary` が追加され、2個になった。fetchサーバーとAWSサーバーを含む全ツール数は7個から8個へ増加した。

  「第2回では何を学びますか？」と質問したところ、次のツール呼び出しを確認できた。

  ```text
  [tool call] glossary_get_lecture_summary({'lecture': 2})

  - 気づき・疑問：
  MCPでは、エージェント側のコードを変更しなくても、サーバー側で新しい関数を公開するだけで、モデルに見えるツールを追加できることが分かった。今回も `app/mcp_server.py` に1行追加しただけで、`glossary_get_lecture_summary` が自動的にツール一覧へ反映された。

  また、Python関数のdocstringと型ヒントがMCP経由でもツールの説明文と引数情報として渡され、モデルは「第2回」という質問から `lecture=2` を正しく指定できた。ツール名に `glossary_` というサーバー名の接頭辞が付くため、複数のMCPサーバーを接続しても名前の衝突を避けられる点も確認できた。

  一方、公開するツールが増えると、各ツールの説明文や引数情報もモデルの入力に含まれる。今回は全ツール数が7個から8個に増え、質問実行時の入力は5,942トークンだった。そのため、利用可能なツールを増やしすぎると、入力トークン数や費用が増えるだけでなく、モデルが用途の似たツールを誤って選ぶ可能性もあると考えた。

  今後の疑問は、複数のMCPサーバーに似た機能のツールが存在する場合、モデルがdocstringだけで適切に使い分けられるかという点である。また、利用者の質問や権限に応じて、モデルへ公開するツールを動的に絞り込む方法も確認したい。


#### 実装

- 取り組んだレベル：実装

- やったこと：
  `app/tools.py` に、指定した講義回の用語から1つをランダムに選び、確認問題と答えをJSON形式で返す `make_quiz` を実装した。講義回に用語がない場合や、0以下の値が指定された場合は例外を発生させず、分かりやすいメッセージを返すようにした。

  さらに、`app/mcp_server.py` に `server.tool()(tools.make_quiz)` を追加し、MCPツールとして公開した。正常入力、存在しない講義回、0以下の講義回に対するテストも追加した。

- 結果：
  MCPエージェントに見えるツール数は8個から9個へ増え、`glossary_make_quiz` が追加された。docstringと型ヒントから、ツールの用途と `lecture` 引数の情報も正しく公開された。

  「第2回の内容から確認問題を1問出して」と質問したところ、次のツール呼び出しを確認した。

  ```text
  [tool call] glossary_make_quiz({'lecture': 2})


- 気づき・疑問：
  `make_quiz` をMCPサーバーで公開すると、エージェント側のコードを変更しなくても、`glossary_make_quiz` として自動的に利用可能になった。docstringと型ヒントから、ツールの説明文と `lecture` 引数の型もモデルへ渡され、第2回と第99回のどちらでも正しい整数が指定された。

  範囲外入力を例外ではなく文字列で返すことで、MCPサーバーを停止させず、モデルが利用者向けの説明へ変換できた。一方、公開ツールが9個に増えたことで、ツール説明も入力に含まれ、入力トークン数が大きくなっている。必要なツールだけを質問や権限に応じて公開する仕組みがあると、費用や誤選択を抑えられるのではないかと疑問に感じた。

#### 発展

- 取り組んだレベル：発展

- やったこと：
  自分が利用しているVS Codeを対象として、MCPサーバーの設定方法をVS Code公式ドキュメントで調査し、演習で使用した `app/mcp_servers.json` と比較した。

  調査日：2026年11月27日

  参照した公式ドキュメント：
  - https://code.visualstudio.com/docs/agent-customization/mcp-servers
  - https://code.visualstudio.com/docs/agents/reference/mcp-configuration

- 結果：
  VS CodeのCopilot用MCP設定は、個人で複数のワークスペースから利用する場合、`$COPILOT_HOME/mcp-config.json` に記載する。`COPILOT_HOME` が未設定の場合は、`~/.copilot/mcp-config.json` を使用する。チームで同じ設定を共有する場合は、ワークスペース直下の `.mcp.json` を使用する。どちらもトップレベルに `mcpServers` を置く。

  コマンドで起動するstdioサーバーは、次のように設定する。

  ```json
  {
    "mcpServers": {
      "playwright": {
        "type": "stdio",
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest"],
        "tools": ["*"]
      }
    }
  }


- 気づき・疑問：
  演習とVS Codeは、どちらも `mcpServers` の下にサーバー名と接続情報を書く点が共通していた。このため、演習で理解した `command`、`args`、`url` の考え方を、VS Codeでもほぼそのまま利用できることが分かった。

  一方、VS Codeには `type`、`tools`、`env`、`cwd`、`headers` など、実際の運用に必要な項目が多く用意されている。特に `tools` で公開ツールを限定できる点は、入力トークン数、モデルによるツールの誤選択、不要な操作のリスクを減らすうえで有効だと考えた。

  また、公式ドキュメントでは、ローカルMCPサーバーは利用者の権限でコードを実行できるため、提供元、起動コマンド、接続先、要求される権限を確認するよう注意されていた。共有する `.mcp.json` に認証情報を直接書かず、環境変数参照を使う必要がある。

  今後の疑問は、同じサーバー設定をPythonエージェントとVS Codeの両方で完全に共有できるかという点である。基本構造は似ているが、VS Code固有の `type`、`tools`、認証方法があるため、共通部分とクライアント固有部分を分離して管理する方法を検討したい。