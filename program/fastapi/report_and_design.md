## DVM-AutoRuneEnhance Management Web

### 目次

### DVM-AutoRuneEnhance Management Web　とは
ゲーム内の装備品(ルーン)を自動で強化するプログラムを補足するためのポータルサイト。  

自動ルーン強化(リンク)の結果を共有し、それに対するユーザのアクションを受け付ける。  
具体的には、自動ルーン強化の結果を掲載し、その情報を元にユーザが不要なルーンを選択。  
その選択に基づいてゲーム画面を操作することでユーザの手間を軽減する。  

副産物としてゲーム内で所有するルーン一覧も閲覧可能。

### 動機

  + 元々こういう風なシステムを作れたら良いなと言う構想があり、これまでの経験によって実現できそうというのがぼんやり感じられたため。
  + 具体的にはサーバからユーザに対してLine Notifyでクエリパラメータ付きURLを発行[^3]すれば、それに基づいてサーバ(ゲーム)を操作できるのでは？という発想。

### 目的

+ ユーザ体験の向上
  - Lineの通知やブラウザ上の操作によってサーバ(ゲーム)を操作できる。
  - 通常取得できないか、取得には非常に手間のかかるルーン一覧を、整形された状態でブラウザで閲覧できる。
+ 技術的挑戦と経験の蓄積
  - Webページの作成
  - WebAPIの作成
  - データベースの利用

上記2つの観点で今回実施したことを以下に分類する。

|実装内容|分類|具体的内容|使用技術・技術要素|
|---:|:---|:---|:---:|
|Webページ|技術的挑戦|・好奇心を満たす。技術的経験を得る。<br>・Webページで結果を見れたらすごい<br>・WebAPIを体験する<br>・Bootstrapを継続して触る<br>・あわよくばJSも扱える|HTML, CSS, JavaScript, Jinja2, FastAPI, Bootstrap|
|自動ルーン強化の結果閲覧|ユーザ体験の向上|直近の自動強化内容を画像とパラメータを添えて表示する|Python|
|ロックの自動解除|・ユーザ体験の向上<br>・技術的挑戦[^1] [^2]|Webページ上のボタンからロックの自動解除ができる。|Python, PyAutoGUI, OpenCV, 状態管理|
|所有ルーン一覧|・ユーザ体験の向上<br>・技術的挑戦|・Webページ上から所有ルーン一覧が閲覧できる<br>・データベースの活用|Python, CSS, MySQL, OCR(Tesseract)|
|サーバの停止|・技術的挑戦|サーバ上からサービス(プロセス)を停止する|Python|


### サイトマップ

![sitemap](https://github.com/StarsandLabo/Python-DVMAutoRuneEnhance/blob/main/program/fastapi/images/sitemap.png)

### 個々のページ解説について

<details><summary>Line Notifyにはこういう通知が届く</summary>

![image](https://github.com/StarsandLabo/Python-DVMAutoRuneEnhance/blob/main/program/fastapi/images/LineNotify_2022-06-13.png)

+ ルーンの強化が一つ終わる度に**強化後の画像**、**かかった推定金額**、**アンロック用のURL** が送られてくる  
  - 今回は動画がないが、アンロック用のURLを選択するとゲーム画面を自動的に操作してアンロックしてくれる。  
   ※強化したけど採用圏外のルーンを探すのは手間なので売れる状態にしてほしい
+ unlock url: から続く内容を選択すると下の図のルーンがロック解除待機のリストに格納される。
+ EstimatedなのはOCRの仕様上100％の精度が出ないため~~画像そのまま送ればいいのでは…~~  
+ スタンプは見た目の区切りをつける目的で入れている。また、サービス側で利用できるものが決まっている。
  - 通常はもっといっぱい強化結果が並ぶので開始終了がどこか分かりづらい。
    - こういう理由もあって、技術的挑戦とあわせて利便性向上するのではと思ったのでポータル作成した。

</details>

<details><summary>最新処理済みルーン一覧</summary>

![image](https://github.com/StarsandLabo/Python-DVMAutoRuneEnhance/blob/main/program/fastapi/images/Screenshot%20from%202022-06-13%2017-03-53.png)

### やりたかったこと

+ 強化後の画像表示
  - スマートフォンからだと画像が小さいため文字情報も付与したかった
+ ボタンクリックでロック解除待ちリストに追加
  - Postメソッドを利用し、ページ遷移をしないようにする[^4]

</details>

<details><summary>対象一覧</summary>

### やりたかったこと

![image](https://github.com/StarsandLabo/Python-DVMAutoRuneEnhance/blob/main/program/fastapi/images/Screenshot%20from%202022-06-13%2017-12-22.png)

+ ロック解除対象の表示
+ ロック解除待ちリストからの削除
+ このページ用意しないでトップページで状態の管理できればよかった
  - 意味がないわけではないと思うけど、あまり必要でもない感じ。
  - とりあえず形にしたくてイケてない実装でもいいやと思ってた。
</details>

<details><summary>所有ルーン一覧</summary>

### やりたかったこと

![image](https://github.com/StarsandLabo/Python-DVMAutoRuneEnhance/blob/main/program/fastapi/images/Screenshot%20from%202022-06-13%2017-18-47.png)

+ 持ってるルーン一覧の表示[^5]
  - 別のOCRプログラムで取得した情報を元にする。
+ 検索機能
  - 未実装

</details>

<details><summary>一覧削除</summary>

### やりたかったこと

![image](https://github.com/StarsandLabo/Python-DVMAutoRuneEnhance/blob/main/program/fastapi/images/Screenshot%20from%202022-06-13%2017-23-25.png)

+ 対象一覧に格納されている内容を一括削除
  - 英語変な気がするけど気にしない。

</details>

<details><summary>作業開始</summary>

### やりたかったこと

![image](https://github.com/StarsandLabo/Python-DVMAutoRuneEnhance/blob/main/program/fastapi/images/Screenshot%20from%202022-06-13%2017-28-48.png)

+ 対象一覧に格納されている内容を元にゲームのロックを解除
  - 今は強化直後の場面でしか解除できないが、理想としてはゲーム内の状態を選ばずにできると良い。  
    ※位置情報を直接送っているので、少しでもルーンの数が変わったりするとNG

</details>

<details><summary>サーバ停止</summary>

### やりたかったこと

![image](https://github.com/StarsandLabo/Python-DVMAutoRuneEnhance/blob/main/program/fastapi/images/Screenshot%20from%202022-06-13%2017-28-52.png)

+ アプリケーションの停止
  - 理屈ではプロセスを停止するだけなので、それをWeb画面からやってみたいと思った。

</details>

### 反省

+ データベースの利用を最初から考えていればよかった。
  - とは言え手探りで色々やって必要性を感じたので今回はこれで良い。  




[^1]:ユーザがAPIを叩く事でサーバ側のGUI操作を自動で行う。
[^2]:探せばあると思うけど、そういうツールは今まで見たことがなかったのでやったらどうなるのかを見てみたかった。
[^3]:LineNotifyからはPostメソッドが利用できないため、クエリパラメータ付きURLを発行することにした。
[^4]:最初はポータルを作るつもりがなく、LineNotifyではPost使えないしクエリパラメータだけで良いと思っていた。Postメソッドの必要性を感じたのは後から
[^5]:ゲームの装備品の情報ってCSVとかテキストで一覧取得できないのは不便だと思う。
