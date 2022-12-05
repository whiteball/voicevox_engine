from pathlib import Path

import yaml
from pydantic import ValidationError

from .Preset import Preset


class PresetLoader:
    def __init__(
        self,
        preset_path: Path,
    ):
        self.presets = []
        self.last_modified_time = 0
        self.preset_path = preset_path

    def load_presets(self):
        """
        プリセットのYAMLファイルを読み込む

        Returns
        -------
        ret: tuple[Preset, str]
            プリセットとエラー文のタプル
        """
        _presets = []

        # 設定ファイルのタイムスタンプを確認
        try:
            _last_modified_time = self.preset_path.stat().st_mtime
            if _last_modified_time == self.last_modified_time:
                return self.presets, ""
        except OSError:
            return None, "プリセットの設定ファイルが見つかりません"

        try:
            with open(self.preset_path, encoding="utf-8") as f:
                obj = yaml.safe_load(f)
                if obj is None:
                    raise FileNotFoundError
        except FileNotFoundError:
            return None, "プリセットの設定ファイルが空の内容です"

        for preset in obj:
            try:
                _presets.append(Preset(**preset))
            except ValidationError:
                return None, "プリセットの設定ファイルにミスがあります"

        # idが一意か確認
        if len([preset.id for preset in _presets]) != len(
            {preset.id for preset in _presets}
        ):
            return None, "プリセットのidに重複があります"

        self.presets = _presets
        self.last_modified_time = _last_modified_time
        return self.presets, ""

    def set_preset(self, preset: Preset):
        """
        YAMLファイルに新規のプリセットを追加する

        Parameters
        ----------
        preset : Preset
            追加するプリセットを渡す

        Returns
        -------
        ret: tuple[int, str]
            追加したプリセットのプリセットIDとエラー文のタプル
        """

        # 手動でファイルが更新されているかも知れないので、最新のYAMLファイルを読み直す
        _, err_detail = self.load_presets()
        if err_detail:
            return -1, err_detail

        # IDが0未満、または存在するIDなら新しいIDを決定し、配列に追加
        if preset.id < 0 or preset.id in {preset.id for preset in self.presets}:
            preset.id = max([preset.id for preset in self.presets]) + 1
        self.presets.append(preset)

        # ファイルに書き込み
        try:
            with open(self.preset_path, mode="w", encoding="utf-8") as f:
                yaml.safe_dump(
                    [vars(preset) for preset in self.presets],
                    f,
                    allow_unicode=True,
                    sort_keys=False,
                )
        except FileNotFoundError:
            self.presets.pop()
            return -1, "プリセットの設定ファイルに書き込み失敗しました"

        return preset.id, ""

    def update_preset(self, preset: Preset):
        """
        YAMLファイルのプリセットを更新する

        Parameters
        ----------
        preset : Preset
            更新するプリセットを渡す

        Returns
        -------
        ret: tuple[int, str]
            更新したプリセットのプリセットIDとエラー文のタプル
        """

        # 手動でファイルが更新されているかも知れないので、最新のYAMLファイルを読み直す
        _, err_detail = self.load_presets()
        if err_detail:
            return -1, err_detail

        # IDが存在するか探索
        for i in range(len(self.presets)):
            if self.presets[i].id == preset.id:
                self.presets[i] = preset
                break
        else:
            return -1, "更新先のプリセットが存在しません"

        # ファイルに書き込み
        try:
            with open(self.preset_path, mode="w", encoding="utf-8") as f:
                yaml.safe_dump(
                    [vars(preset) for preset in self.presets],
                    f,
                    allow_unicode=True,
                    sort_keys=False,
                )
        except FileNotFoundError:
            return -1, "プリセットの設定ファイルに書き込み失敗しました"

        return preset.id, ""

    def delete_preset(self, id: int):
        """
        YAMLファイルのプリセットを更新する

        Parameters
        ----------
        id: int
            更新するプリセットを渡す

        Returns
        -------
        ret: tuple[int, str]
            更新したプリセットのプリセットIDとエラー文のタプル
        """

        # 手動でファイルが更新されているかも知れないので、最新のYAMLファイルを読み直す
        _, err_detail = self.load_presets()
        if err_detail:
            return -1, err_detail

        # IDが存在するか探索
        buf = None
        buf_index = -1
        for i in range(len(self.presets)):
            if self.presets[i].id == id:
                buf = self.presets.pop(i)
                buf_index = i
                break
        else:
            return -1, "削除対象のプリセットが存在しません"

        # ファイルに書き込み
        try:
            with open(self.preset_path, mode="w", encoding="utf-8") as f:
                yaml.safe_dump(
                    [vars(preset) for preset in self.presets],
                    f,
                    allow_unicode=True,
                    sort_keys=False,
                )
        except FileNotFoundError:
            self.presets.insert(buf_index, buf)
            return -1, "プリセットの設定ファイルに書き込み失敗しました"

        return id, ""
