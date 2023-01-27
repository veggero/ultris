import QtMultimedia 5.15
import QtQuick 2.6
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.12
import QtQuick.Layouts 1.2

ApplicationWindow {
    id: root
    visible: true
    minimumWidth: 1000
    maximumWidth: minimumWidth
    minimumHeight: 1000
    maximumHeight: minimumHeight

    Rectangle {
        id: background
        anchors.fill: parent
        color: "#edebe9"

        focus: true
        Keys.onPressed: (event)=> {
            if (event.key == Qt.Key_Left) {
                py.back()
                event.accepted = true;
            }
            if (event.key == Qt.Key_Right) {
                py.forward()
                event.accepted = true;
            }
            if (event.key == Qt.Key_Up) {
                py.prev_line()
                event.accepted = true;
            }
            if (event.key == Qt.Key_Down) {
                py.next_line()
                event.accepted = true;
            }
            if (event.key == Qt.Key_Backspace) {
                py.delete()
                event.accepted = true;
            }
        }
    }

    property string position: py.png
    property string moves: py.moves
    property var positionEval: py.evaluation
    property var depth: py.depth
    property var bestmove: py.best_move
    property bool allboards: py.allboards

    onPositionEvalChanged: {
        if (positionEval >= 0) {
            evaltext.anchors.top = xbar.top
            evaltext.anchors.bottom = undefined
        } else {
            evaltext.anchors.top = undefined
            evaltext.anchors.bottom = xbar.top
        }
    }

    Item {
        id: evalBar
        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
        }
        width: 50

        Rectangle {
            id: xbar
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: parent.height/2 + parent.height/200*positionEval
            color: "#bab5f0"
        }

        Rectangle {
            id: ybar
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
            }
            height: parent.height/2 - parent.height/200*positionEval
            color: "#f0b5b5"
        }

        Rectangle {
            anchors {
                left: parent.left
                right: parent.right
                top: xbar.top
            }
            color: "gray"
            height: 2
        }

        Text {
            id: evaltext
            anchors {
                top: positionEval >= 0 ? xbar.top : undefined
                bottom: positionEval < 0 ? ybar.bottom : undefined
                horizontalCenter: xbar.horizontalCenter
                topMargin: 10
                bottomMargin: 10
            }
            text: (positionEval > 0 ? '+' : '') + positionEval + '\nd' + depth
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 15
            color: positionEval <= 0 ? "#854848" : '#444480'
        }
    }

    DropShadow {
        anchors.fill: grid
        radius: 10.0
        samples: 17
        color: "#50000000"
        source: grid
    }

    GridLayout {
        id: grid
        anchors{
            top: parent.top
            right: parent.right
            left: evalBar.right
            bottom: movesPanel.top
            topMargin: 15
            bottomMargin: 15
            leftMargin: 30
            rightMargin: 30
        }
        columns: 3

        Repeater {
            model: 9

            GridLayout {
                id: board
                property string boardstr: position[2+cellx]
                property int cellx: index
                Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                rowSpacing: 0
                columnSpacing: 0
                columns: 3

                Repeater {
                    model: 9


                    Rectangle {
                        property int celly: index
                        width: 80
                        height: 80
                        property var colors: ({
                            '.': {'dark': '#f0d9b5', 'light': '#b58863'},
                            '@': {'dark': '#f0d9b5', 'light': '#b58863'},
                            'X': {'dark': '#bab5f0', 'light': '#6364b5'},
                            'O': {'dark': '#f0b5b5', 'light': '#b56363'}
                        })
                        property string here: position[12+cellx*10+celly]
                        color: (celly + cellx) % 2 ? colors[boardstr]['dark'] : colors[boardstr]['light']

                        Image {
                            anchors {
                                fill: parent
                                topMargin: 8
                                bottomMargin: 8
                                leftMargin: 8
                                rightMargin: 8
                            }
                            source: "assets/x.png"
                            mipmap: true
                            visible: here == 'X'
                        }

                        Image {
                            anchors {
                                fill: parent
                                topMargin: 8
                                bottomMargin: 8
                                leftMargin: 8
                                rightMargin: 8
                            }
                            source: "assets/o.png"
                            mipmap: true
                            visible: here == 'O'
                        }

                        Rectangle {
                            id: greendot
                            anchors {
                                fill: parent
                                topMargin: 30
                                bottomMargin: 30
                                leftMargin: 30
                                rightMargin: 30
                            }
                            color: "#50629924"
                            radius: 50
                            visible: here == '.' && (boardstr == '@' || (allboards && boardstr == '.'))
                        }

                        Rectangle {
                            anchors {
                                fill: parent
                                topMargin: 30
                                bottomMargin: 30
                                leftMargin: 30
                                rightMargin: 30
                            }
                            color: "#a03a4c99"
                            radius: 50
                            visible: bestmove == 'abcdefghi'[cellx] + 'abcdefghi'[celly]
                        }

                        MouseArea {
                            anchors.fill: parent
                            enabled: greendot.visible
                            onClicked: py.add_move(cellx, celly)
                        }

                    }
                }
            }
        }
    }

    Item {
        id: movesPanel
        anchors {
            left: evalBar.right
            right: parent.right
            bottom: parent.bottom
        }

        height: 180

        Rectangle {
            anchors.fill: parent
            color: "white"
        }

        Rectangle {
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
            }
            height: 1
            color: "gray"
        }

        Text {
            anchors {
                fill: parent
                leftMargin: 20
                rightMargin: 20
                bottomMargin: 20
            }
            text: moves
            wrapMode: Text.WordWrap
            textFormat: Text.RichText
            font.pixelSize: 20
            verticalAlignment: Text.AlignVCenter

            lineHeight: 1.5
            font.wordSpacing: 5

            onLinkActivated: {
                py.link(link)
            }
        }
    }
}
